"""Real localhost FastAPI requests with generated data and synthetic runtimes."""
import http.client
import json
import socket
import threading
import time
import pytest
import uvicorn
from src.tabular import api
from src.tabular.questionnaire_explain import EXAMPLE_PROFILE, QuestionnairePrototype, fit_support
from src.tabular.xgboost_comparison_nhanes import make_xgboost_pipeline
from test_questionnaire_explain import generated_inputs
from test_photo_explanation import generated_jpeg


class GeneratedRuntime:
    def status(self): return {'ready':True,'synthetic_only':True}
    def explain(self,payload):
        if payload!=b'generated': raise ValueError('Unregistered generated input')
        return {'synthetic_only':True,'predicted_grade':2,'explained_grade':2}


@pytest.fixture(scope='module')
def servers():
    x,y=generated_inputs();model=make_xgboost_pipeline(('Full','A'));model.fit(x,y)
    prototype=QuestionnairePrototype(model,fit_support(x),{'final_model':False,'held_out_evaluated':False})
    items=[]
    for runtime in (None,GeneratedRuntime()):
        app=api.create_app(prototype,vision_runtime=runtime,
                           vision_evidence={'scope':'generated_aggregate_fixture','test_used':False} if runtime else None,
                           questionnaire_evidence={'model_id':prototype.model_id,'scope':'generated'} if runtime else None)
        sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,access_log=False,log_level='critical'))
        thread=threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True);thread.start()
        for _ in range(100):
            if server.started: break
            time.sleep(.01)
        assert server.started
        items.append((port,server,thread))
    yield [row[0] for row in items],prototype
    for port,server,thread in items:
        server.should_exit=True;thread.join(timeout=5)
        assert not thread.is_alive()


def request(port,path,data=None,headers=None,raw=None):
    connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
    body=raw if raw is not None else json.dumps(data) if data is not None else None
    h={'X-Component2-Demo':'1','Content-Type':'application/json',**(headers or {})}
    connection.request('POST' if body is not None else 'GET',path,body,h)
    response=connection.getresponse();content=response.read();status=response.status
    result=json.loads(content) if 'application/json' in response.getheader('Content-Type','') else content
    connection.close();return status,result


def test_live_shap_scenario_reset_matches_existing_functions(servers):
    (port,_),prototype=servers
    code,result=request(port,'/api/predict',{'profile':EXAMPLE_PROFILE})
    assert code==200 and result==prototype.predict(EXAMPLE_PROFILE)
    payload={'original':EXAMPLE_PROFILE,'model_id':prototype.model_id}
    code,changed=request(port,'/api/what-if',{**payload,'changes':{'OHQ870':7}})
    assert code==200 and changed==prototype.simulate(EXAMPLE_PROFILE,{'OHQ870':7},prototype.model_id)
    code,reset=request(port,'/api/reset',payload)
    assert code==200 and reset['scenario']==result and reset['is_reset']


@pytest.mark.parametrize('fault',['outcome','protected','version','nan','extra','duplicate','large','type'])
def test_api_validation_fail_closed(servers,fault):
    (port,_),prototype=servers
    route='/api/predict'; body={'profile':dict(EXAMPLE_PROFILE)};raw=None
    if fault=='outcome': body['profile']['OHQ850']=1
    if fault=='protected': route='/api/what-if';body={'original':EXAMPLE_PROFILE,'model_id':prototype.model_id,'changes':{'RIDAGEYR':40}}
    if fault=='version': route='/api/reset';body={'original':EXAMPLE_PROFILE,'model_id':'stale'}
    if fault=='nan':body['profile']['RIDAGEYR']=float('nan')
    if fault=='extra':body['secret']=123
    if fault=='duplicate':raw='{"profile":{},"profile":{}}'
    if fault=='large':raw='x'*8193
    if fault=='type':body={'profile':[]}
    assert request(port,route,body,raw=raw)[0]==422


def test_local_security_contract_and_frontend(servers):
    (port,_),_=servers
    assert request(port,'/api/schema',headers={'Host':'evil.example'})[0]==403
    assert request(port,'/api/predict',{},headers={'Origin':'https://evil.example'})[0]==403
    assert request(port,'/api/predict',{},headers={'X-Component2-Demo':'0'})[0]==415
    assert request(port,'/api/schema')[0]==200
    assert b'app.js' in request(port,'/')[1]
    assert request(port,'/app.js')[0]==200
    assert request(port,'/openapi.json')[1]['paths']['/api/predict']['post']['requestBody']['required']
    for path in ('/data/Test','/vision/unknown.png','/../AGENTS.md','/models/x.pt'):
        assert request(port,path)[0]==404


def test_photo_inactive_and_registered_synthetic_route(servers):
    (inactive,active),_=servers
    assert request(inactive,'/api/vision/runtime')[1]['ready'] is False
    assert request(inactive,'/api/vision/photo',raw=b'not decoded',headers={'Content-Type':'image/jpeg'})[0]==503
    assert request(active,'/api/vision/photo',raw=b'generated',headers={'Content-Type':'image/jpeg'})[1]['synthetic_only']
    assert request(active,'/api/vision/photo',raw=b'other',headers={'Content-Type':'image/jpeg'})[0]==422
    assert request(active,'/api/vision/photo',raw=b'generated')[0]==422


def test_aggregate_evidence_endpoint_is_separate_and_fail_closed(servers):
    (inactive,active),_=servers
    assert request(inactive,'/api/vision/evidence')[0]==503
    code,result=request(active,'/api/vision/evidence')
    assert code==200 and result=={'scope':'generated_aggregate_fixture','test_used':False}


def test_questionnaire_evidence_is_unavailable_or_matches_running_model(servers):
    (inactive,active),prototype=servers
    assert request(inactive,'/api/questionnaire/evidence')[0]==503
    code,result=request(active,'/api/questionnaire/evidence')
    assert code==200 and result=={'scope':'generated','model_id':prototype.model_id}
