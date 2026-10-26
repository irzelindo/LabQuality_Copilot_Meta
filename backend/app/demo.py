from datetime import timedelta
from sqlalchemy import select
from .models import *
from .schemas import ActionIn, AssessmentIn
from .security import passwords
from .services import import_assessments

DEMO_NAME = "Rede de demonstração LabQuality"
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


def seed_demo(db, password: str):
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
    instrument = Instrument(organization_id=org.id, code="DEMO-QMS", version="1.0", name="DEMO-QMS · instrumento fictício",
        description="Rubrica original de demonstração. Não representa SLIPTA, ISO 15189 ou acreditação.",
        criteria=[{"code": f"C{i + 1:02d}", "section": s, "title": t, "maximum": 2, "critical": i == 3} for i, (s, t) in enumerate(CRITERIA)])
    db.add(instrument)
    db.flush()
    result = import_assessments(db, users["admin"], sample_assessments())
    for code, title, criteria, content in PROCEDURES:
        db.add(Document(organization_id=org.id, scope_key="organization", code=code, revision=1,
            title=title, content=content, criterion_codes=criteria, status="published",
            author_id=users["quality"].id, reviewer_id=users["verifier"].id))
    from .api import create_action
    finding = db.scalar(select(Finding).join(Assessment, Finding.assessment_id == Assessment.id).where(
        Assessment.laboratory_id == labs["SUL"].id, Assessment.assessment_date == "2026-10-01", Finding.criterion_code == "C04"))
    action = create_action(ActionIn(finding_id=finding.id, title="Regularizar o registo de verificação do equipamento",
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
