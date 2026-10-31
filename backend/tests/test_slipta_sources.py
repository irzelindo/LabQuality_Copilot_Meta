import openpyxl
import pytest
from pypdf import PdfWriter
from app.slipta_sources import catalog, prepare_pack
from app.reference_packs import ReferencePack


def form(path, missing=False):
    wb=openpyxl.Workbook(); s=wb.active; s.title='survey'
    s.append(['type','name','label','calculation'])
    s.append(['begin_group','tt_pp_02_s1','SECÇÃO 1',None])
    s.append(['note','p2_s1_1_2_note','**1.2 Políticas**\nPontuação total: 3 Pontos',None])
    s.append(['select_one answers','p2_s1_1_2_a','a. Política documentada',None])
    s.append(['select_one answers','p2_s1_1_2_b','b. Revisão independente',None])
    s.append(['calculate','p2_s1_1_2_calculate',None,'expression'])
    s.append(['select_one answers','p2_s12_12_24','**12.24 Biossegurança**',None])
    s.append(['calculate','p2_s12_12_24_calculate',None,'unknown' if missing else "if(selected(${p2_s12_12_24}, 'sim'), 2, 0)"])
    settings=wb.create_sheet('settings'); settings.append(['form_title','form_id','version']); settings.append(['SLIPTA','slipta-test','v1'])
    wb.save(path)


def test_grouped_aliases_and_calculated_weight(tmp_path):
    x=tmp_path/'form.xlsx'; form(x); data=catalog(x)
    assert len(data['items'])==2 and data['maximum']==5
    assert len(data['items'][0]['answer_fields'])==2
    assert 'Revisão independente' in data['items'][0]['content']
    assert data['items'][1]['weight_origin']=='explicit_yes_calculation'


def test_unknown_weight_stops_without_guessing(tmp_path):
    x=tmp_path/'form.xlsx'; form(x,True)
    with pytest.raises(ValueError,match='Pontuação máxima'): catalog(x)


def test_reference_pack_provenance_and_draft_only_payload(tmp_path):
    x=tmp_path/'form.xlsx'; form(x)
    pdf=tmp_path/'source.pdf'; w=PdfWriter(); w.add_blank_page(width=500,height=700)
    with pdf.open('wb') as f: w.write(f)
    pack=ReferencePack.model_validate(prepare_pack(pdf,x))
    assert len(pack.documents)==2 and len(pack.provenance['pdf_sha256'])==64
    assert 'p2_s1_1_2_b' in pack.documents[0].criterion_codes
    assert 'não é um procedimento local' in pack.documents[0].content
    assert 'status' not in pack.documents[0].model_dump()
