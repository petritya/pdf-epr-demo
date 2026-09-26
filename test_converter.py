import io
import zipfile
from openpyxl import load_workbook
from pypdf import PdfWriter
from fastapi.testclient import TestClient
import pytest
from converter import collect_pdfs, split_pages, convert, PageData, Table
from webapp import app

def pdf(n=1):
    writer=PdfWriter()
    for _ in range(n): writer.add_blank_page(width=100,height=100)
    out=io.BytesIO();writer.write(out);return out.getvalue()

def sample(_):
    return PageData(tables=[Table(title='Tételek',columns=['Kód','Érték'],rows=[['00123','=HYPERLINK("x")']])],other_text='Megjegyzés',warnings=['Olvasási bizonytalanság'])

def test_xlsx_preserves_identifiers_and_disables_formulas():
    name,data,mime=convert(split_pages(collect_pdfs([('a.pdf',pdf())])),extractor=sample)
    wb=load_workbook(io.BytesIO(data))
    assert name=='01_a.xlsx'
    assert wb['Táblázat_1']['C2'].value=='00123'
    assert wb['Táblázat_1']['D2'].data_type=='s'
    assert wb['Szöveg']['C2'].value=='Megjegyzés'
    assert wb['Ellenőrzések']['C3'].value=='Olvasási bizonytalanság'

def test_multiple_documents_distinct_outputs():
    _,data,mime=convert(split_pages(collect_pdfs([('a.pdf',pdf()),('a.pdf',pdf())])),extractor=sample)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.namelist()==['01_a.xlsx','02_a.xlsx']

def test_zip_traversal_rejected():
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:z.writestr('../a.pdf',pdf())
    with pytest.raises(ValueError):collect_pdfs([('a.zip',out.getvalue())])

def test_page_limit():
    with pytest.raises(ValueError):split_pages([('a.pdf',pdf(11))])

def test_invalid_pdf():
    with pytest.raises(ValueError):collect_pdfs([('a.pdf',b'not PDF')])

def test_valid_zip():
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as z:z.writestr('folder/a.pdf',pdf())
    assert len(split_pages(collect_pdfs([('a.zip',out.getvalue())])))==1

def test_unconfigured_service_cannot_send_data(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with TestClient(app) as c:
        assert c.get('/').status_code==200
        assert not c.get('/config').json()['ready']
        assert c.post('/jobs',files={'files':('a.pdf',pdf(),'application/pdf')},data={'consent':'yes'}).status_code==503

def test_full_flow_with_fake_extractor(monkeypatch):
    import webapp
    monkeypatch.setenv('OPENAI_API_KEY','test-not-real')
    monkeypatch.setenv('PRIVACY_URL','https://example.com/privacy')
    monkeypatch.setattr(webapp,'convert',lambda docs,progress:convert(docs,extractor=sample,progress=progress))
    with TestClient(app) as c:
        res=c.post('/jobs',files={'files':('a.pdf',pdf(),'application/pdf')},data={'consent':'yes'})
        assert res.status_code==202
        token=res.json()['id']
        import time
        for _ in range(100):
            s=c.get('/jobs/'+token).json()
            if s['state']=='done':break
            time.sleep(.01)
        assert s['state']=='done'
        assert c.get('/jobs/'+token+'/download').status_code==200
        assert 'data' not in s
        assert c.get('/jobs/unknown/download').status_code==404
