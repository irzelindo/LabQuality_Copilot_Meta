from datetime import timedelta
from pathlib import Path
import hashlib
import json
from sqlalchemy import delete, select
from .models import *
from .schemas import ActionIn, AssessmentIn
from .security import passwords
from .services import import_assessments

DEMO_NAME = "Rede de demonstração LabQuality"
PILOT = json.loads((Path(__file__).parent / "slipta_pilot.json").read_text(encoding="utf-8"))
SCENARIOS = {
    "SUL": {
        "5.12": ("A manutenção preventiva da centrífuga não tem registo assinado para o trimestre.", [0, 1, 2]),
        "8.19": ("O frigorífico de reagentes registou excursão de temperatura sem avaliação do impacto nos lotes.", [0, 1, 1]),
        "8.15": ("Foi libertado um lote de resultados sem evidência da revisão do controlo interno do dia.", [0, 1, 2]),
        "10.1": ("O desvio não foi formalmente investigado nem associado a uma acção correctiva.", [0, 0, 1]),
    },
    "CENTRO": {
        "1.8": ("Foi encontrada uma instrução de trabalho revogada junto do equipamento em uso.", [0, 1, 2]),
        "3.10": ("Não há registo de competência actualizado para dois técnicos que validam resultados.", [0, 1, 1]),
        "8.10": ("Três amostras remetidas ao laboratório de referência não têm seguimento documentado.", [0, 0, 1]),
        "9.4": ("Uma alteração de resultado não conserva o motivo, a hora e a identidade do autor.", [0, 1, 1]),
    },
    "NORTE": {
        "7.6": ("O inventário não identifica claramente os lotes e as datas de validade dos reagentes.", [0, 1, 2]),
        "8.3": ("Foram observadas requisições sem dois identificadores concordantes na recepção.", [0, 0, 1]),
        "8.20": ("A avaliação externa da qualidade apresenta desempenho insatisfatório sem investigação registada.", [0, 1, 1]),
        "12.13": ("Os contentores de perfurocortantes foram encontrados acima do limite de enchimento.", [0, 1, 2]),
    },
}
BACKGROUND_THRESHOLD = {"SUL": (8, 6, 4), "CENTRO": (6, 8, 7), "NORTE": (9, 8, 8)}
PILOT_DOCUMENTS = [
    ("PILOTO-EQP", "Equipamento, temperatura e controlo — exemplo", ["5.12", "8.19", "8.15"],
     "Documento ilustrativo, não é um procedimento institucional aprovado. Registe a manutenção preventiva com data, responsável e resultado. "
     "Investigue excursões de temperatura e documente a decisão sobre os reagentes afectados. "
     "Revise os controlos internos antes de libertar resultados e registe qualquer desvio."),
    ("PILOTO-DOC", "Documentos, competências e rastreabilidade — exemplo", ["1.8", "3.10", "8.10", "9.4"],
     "Documento ilustrativo, não é um procedimento institucional aprovado. Retire instruções revogadas dos locais de trabalho. "
     "Documente a avaliação de competência antes de autorizar tarefas. "
     "Mantenha rastreio de amostras encaminhadas e dos resultados recebidos. "
     "Registe autor, hora e motivo de cada alteração de resultado."),
    ("PILOTO-SUP", "Inventário, amostras e segurança — exemplo", ["7.6", "8.3", "8.20", "12.13"],
     "Documento ilustrativo, não é um procedimento institucional aprovado. Registe lote e validade dos reagentes no inventário. "
     "Confirme os identificadores da amostra na recepção. "
     "Investigue resultados insatisfatórios da avaliação externa e acompanhe a acção. "
     "Substitua contentores de perfurocortantes antes do limite de enchimento."),
    ("PILOTO-CAPA", "Investigação e eficácia — exemplo", ["10.1", "11.1"],
     "Documento ilustrativo, não é um procedimento institucional aprovado. Registe o trabalho não conforme, avalie o impacto, "
     "investigue a causa e atribua responsável e prazo à acção. Verifique a eficácia antes do encerramento."),
]
VECTORS = {
    "SUL": [[1,1,1,0,1,1,1,1,1,1], [2,1,2,0,1,1,2,1,1,1], [2,2,2,0,2,2,2,1,2,1]],
    "CENTRO": [[2,2,2,2,2,1,2,1,1,1], [2,1,2,1,1,1,2,1,1,1], [1,1,1,1,1,1,1,1,1,1]],
    "NORTE": [[2,1,1,2,1,1,1,1,1,1], [1,2,1,2,1,1,1,1,1,1], [1,1,2,2,1,1,1,1,1,1]]
}
CRITERIA = [
    ("Documentação", "Os procedimentos em uso têm uma versão identificada."),
    ("Documentação", "Os documentos retirados estão separados dos documentos em vigor."),
    ("Equipamentos", "O inventário identifica responsáveis e prazos de manutenção."),
    ("Equipamentos", "A verificação do equipamento está registada e revista."),
    ("Competências", "As competências necessárias para cada tarefa estão identificadas."),
    ("Competências", "A formação e a verificação de competências têm registos."),
    ("Processos", "Os registos permitem acompanhar a execução do processo."),
    ("Processos", "As ocorrências são registadas e investigadas."),
    ("Melhoria", "As acções têm responsável, prazo e acompanhamento."),
    ("Melhoria", "A eficácia é verificada antes do encerramento das acções.")
]
PROCEDURES = [
    ("DEMO-DOC-01", "Controlo documental — exemplo fictício", ["C01", "C02"],
     "Este é um procedimento fictício para demonstração. Identifique a versão e o responsável de cada documento. "
     "Antes da publicação, uma pessoa diferente do autor revê e aprova o conteúdo. "
     "Quando uma nova versão entra em vigor, retire a versão anterior dos locais de utilização e registe a substituição."),
    ("DEMO-EQP-01", "Verificação de equipamento — exemplo fictício", ["C03", "C04"],
     "Este é um procedimento fictício para demonstração. Registe a identificação do equipamento, a data, o resultado "
     "da verificação e o responsável. Se o resultado não cumprir o critério local acordado, registe a ocorrência, "
     "avalie o impacto e atribua uma acção. A utilização após uma falha depende da decisão de um responsável autorizado. "
     "Uma segunda pessoa deve rever o registo da verificação e as evidências da correcção."),
    ("DEMO-CAPA-01", "Acções e eficácia — exemplo fictício", ["C05", "C06", "C07", "C08", "C09", "C10"],
     "Este é um procedimento fictício para demonstração. Investigue a causa do achado antes de escolher a acção. "
     "Cada acção deve identificar um responsável, um prazo e um critério de conclusão verificável. "
     "Anexe evidências da execução e peça a outra pessoa que avalie a eficácia. "
     "Se a acção não resolver a causa, reabra o registo, justifique a decisão e reveja o plano. "
     "Para competências, descreva a tarefa e registe o resultado da observação por um supervisor.")
]


def sample_assessments():
    records = []
    for lab, vectors in VECTORS.items():
        for i, vector in enumerate(vectors):
            records.append(AssessmentIn(source="demo", external_id=f"{lab}-{i + 1}", source_revision="1",
                laboratory_code=lab, instrument_code="DEMO-QMS", instrument_version="1.0",
                assessment_date=f"2026-{8 + i:02d}-01", answers={f"C{j + 1:02d}": {"value": v, "comment": "Dados fictícios."} for j, v in enumerate(vector)}))
    return records


def pilot_assessments():
    """Nine labelled simulations, three separate assessment dates per lab."""
    records = []
    for lab, issues in SCENARIOS.items():
        for moment, date_text in enumerate(("2026-08-12", "2026-09-15", "2026-10-20")):
            answers = {}
            for criterion in PILOT["criteria"]:
                code, maximum = criterion["code"], criterion["maximum"]
                if code in issues:
                    observation, progression = issues[code]
                    value = min(progression[moment], maximum)
                    comment = "Cenário simulado: " + observation + (" Acção ainda por verificar." if value < maximum else " Melhoria documentada no cenário.")
                else:
                    # A reproducible background of incomplete records makes all twelve sections informative.
                    bucket = int(hashlib.sha256(f"{lab}:{code}".encode()).hexdigest()[:4], 16) % 11
                    value = max(0, maximum - (maximum if bucket == 0 else 1)) if bucket < BACKGROUND_THRESHOLD[lab][moment] else maximum
                    comment = ("Cenário simulado: evidência parcial; o auditor deve confirmar o registo referente a " + criterion["title"] + ".") if value < maximum else "Cenário simulado: evidência observada."
                answers[code] = {"value": value, "comment": comment}
            records.append(AssessmentIn(source="demo", external_id=f"{lab}-{moment + 1}",
                source_revision="piloto-2026.10", laboratory_code=lab,
                instrument_code=PILOT["instrument_code"], instrument_version=PILOT["instrument_version"],
                assessment_date=date_text, answers=answers,
                reason="Cenário simulado baseado nos temas do XLSForm SLIPTA; não é auditoria de um laboratório real."))
    return records


def seed_demo(db, password: str, scenario: str = "slipta"):
    existing = db.scalar(select(Organization).where(Organization.name == DEMO_NAME))
    if existing:
        return {"already_exists": True, "organization_id": existing.id}
    if len(password) < 12:
        raise ValueError("Defina LQ_DEMO_PASSWORD com pelo menos 12 caracteres.")
    org = Organization(name=DEMO_NAME)
    db.add(org)
    db.flush()
    labs = {}
    for code, name, region in [("SUL", "Laboratório Sul", "Região Sul"), ("CENTRO", "Laboratório Centro", "Região Centro"), ("NORTE", "Laboratório Norte", "Região Norte")]:
        row = Laboratory(organization_id=org.id, code=code, name=name, region=region)
        db.add(row)
        db.flush()
        labs[code] = row
    digest = passwords.hash(password)
    accounts = [
        ("admin@labquality.local", "Administrador da demonstração", "admin", []),
        ("qualidade@labquality.local", "Responsável de qualidade Sul", "quality", [labs["SUL"].id]),
        ("gestor@labquality.local", "Gestor do laboratório Sul", "manager", [labs["SUL"].id]),
        ("verificador@labquality.local", "Verificador da rede", "verifier", [l.id for l in labs.values()]),
        ("coordenacao@labquality.local", "Coordenação da rede", "coordinator", []),
        ("parceiro@labquality.local", "Parceiro da demonstração", "partner", [])
    ]
    users = {}
    for email, name, role, lab_ids in accounts:
        user = User(organization_id=org.id, email=email, name=name, role=role, laboratory_ids=lab_ids, password_hash=digest)
        db.add(user)
        db.flush()
        users[role] = user
    legacy = scenario == "legacy"
    instrument = (Instrument(organization_id=org.id, code="DEMO-QMS", version="1.0", name="DEMO-QMS · instrumento fictício",
        description="Rubrica original de demonstração. Não representa SLIPTA, ISO 15189 ou acreditação.",
        criteria=[{"code": f"C{i + 1:02d}", "section": s, "title": t, "maximum": 2, "critical": i == 3} for i, (s, t) in enumerate(CRITERIA)]) if legacy else
        Instrument(organization_id=org.id, code=PILOT["instrument_code"], version=PILOT["instrument_version"],
        name="Checklist SLIPTA ODK · piloto demonstrativo",
        description="151 itens/365 pontos do XLSForm fornecido. Pontuação provisória; divergência face ao resumo 145/373. Sem classificação oficial.",
        scoring_rule="sum_applicable_v1",
        criteria=[{key: c[key] for key in ("code", "section", "title", "maximum", "critical")} for c in PILOT["criteria"]]))
    db.add(instrument)
    db.flush()
    import_assessments(db, users["admin"], sample_assessments() if legacy else pilot_assessments())
    for code, title, criteria, content in (PROCEDURES if legacy else PILOT_DOCUMENTS):
        db.add(Document(organization_id=org.id, scope_key="organization", code=code, revision=1,
            title=title, content=content, criterion_codes=criteria, status="published",
            author_id=users["quality"].id, reviewer_id=users["verifier"].id))
    from .api import create_action
    finding = db.scalar(select(Finding).join(Assessment, Finding.assessment_id == Assessment.id).where(
        Assessment.laboratory_id == labs["SUL"].id, Assessment.assessment_date == ("2026-10-01" if legacy else "2026-10-20"),
        Finding.criterion_code == ("C04" if legacy else "8.19")))
    action = create_action(ActionIn(finding_id=finding.id, title="Regularizar o registo de verificação do equipamento" if legacy else "Investigar excursão de temperatura no frigorífico de reagentes",
          description="Investigar a ausência de registos, acordar o procedimento e reunir evidências de execução.",
          cause="Causa por investigar com a equipa.", priority="critical", owner_id=users["quality"].id,
          due_date=(now() + timedelta(days=7)).date()), db, users["admin"])
    action.status = "approved"
    for kind, title, details in [
        ("risk", "Ausência de registo de verificação", {"likelihood": 3, "impact": 4}),
        ("occurrence", "Registo incompleto identificado na avaliação", {"category": "documentation"}),
        ("competency", "Observação da execução do procedimento", {"task": "Verificação de equipamento"}),
        ("equipment", "Equipamento de demonstração EQ-001", {"asset_code": "EQ-001", "activity": "Verificação periódica"})]:
        db.add(Register(organization_id=org.id, laboratory_id=labs["SUL"].id, kind=kind, title=title,
                        description="Registo fictício para demonstração.", owner_id=users["quality"].id,
                        due_date=(now() + timedelta(days=14)).date().isoformat(), details=details))
    db.flush()
    return {"organization_id": org.id, "assessments": 9, "users": [a[0] for a in accounts]}


def refresh_demo(db, password: str):
    """Replace only the isolated demo organization; refuse any imported ODK/manual assessment."""
    org = db.scalar(select(Organization).where(Organization.name == DEMO_NAME))
    evidence_keys = []
    if org:
        roots = list(db.scalars(select(AssessmentRoot).where(AssessmentRoot.organization_id == org.id)))
        if any(root.source != "demo" for root in roots):
            raise ValueError("A organização de demonstração contém avaliações não demonstrativas. Limpeza recusada.")
        expected_emails = {"admin@labquality.local", "qualidade@labquality.local", "gestor@labquality.local",
                           "verificador@labquality.local", "coordenacao@labquality.local", "parceiro@labquality.local"}
        users = list(db.scalars(select(User).where(User.organization_id == org.id)))
        if {u.email for u in users} != expected_emails:
            raise ValueError("A organização de demonstração contém contas alteradas. Limpeza recusada.")
        evidence_keys = list(db.scalars(select(Evidence.storage_key).where(Evidence.organization_id == org.id)))
        # All rows are scoped to this exact organization. Other organizations remain untouched.
        for model in (Verification, Evidence, Action, Finding, AIExecution, Assessment, AssessmentRoot,
                      ImportRun, Job, Register, Notification, Document, Instrument, AuditEvent):
            db.execute(delete(model).where(model.organization_id == org.id))
        db.execute(delete(ODKSyncConfig).where(ODKSyncConfig.organization_id == org.id))
        for user in users:
            db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
        for model in (User, Laboratory):
            db.execute(delete(model).where(model.organization_id == org.id))
        db.delete(org)
        db.flush()
    return {**seed_demo(db, password), "deleted_evidence_keys": evidence_keys}
