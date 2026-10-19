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


class GeneratedROIRuntime:
    def status(self): return {'ready':True,'synthetic_only':True,'fold':0,'device':'cpu'}
    def predict(self,payload):
        if payload!=b'generated': raise ValueError('Unregistered generated input')
        return {'synthetic_only':True,'image_mgi_grade':3,'no_detection':False,
                'detections':[{'grade':3,'detector_confidence':0.91}],
                'overlay_png_base64':'generated-overlay'}


class GeneratedLocalUploadRuntime:
    def status(self):
        return {'ready':True,'upload_mode':'local_user_upload_demo','synthetic_only':False}
    def explain_upload(self,payload,content_type):
        if payload!=b'generated' or content_type not in ('image/jpeg','image/png','image/webp'):
            raise ValueError('Generated upload fixture only')
        return {'upload_mode':'local_user_upload_demo','predicted_grade':2,'photo_saved':False}


class GeneratedLocalUploadROIRuntime:
    def status(self):
        return {'ready':True,'upload_mode':'local_user_upload_demo','fold':0,'device':'cpu'}
    def predict_upload(self,payload,content_type):
        if payload!=b'generated' or content_type not in ('image/jpeg','image/png','image/webp'):
            raise ValueError('Generated upload fixture only')
        return {'upload_mode':'local_user_upload_demo','image_mgi_grade':3,
                'no_detection':False,'detections':[{'grade':3,'detector_confidence':0.91}],
                'overlay_png_base64':'generated-overlay','photo_saved':False}


class GeneratedLocalUploadROIV1Runtime:
    def status(self):
        return {'ready':True,'upload_mode':'local_user_upload_demo','fold':0,'device':'cpu'}
    def predict_upload(self,payload,content_type):
        if payload!=b'generated' or content_type not in ('image/jpeg','image/png','image/webp'):
            raise ValueError('Generated upload fixture only')
        return {'model_family':'roi_tooth_v1','upload_mode':'local_user_upload_demo',
                'image_mgi_grade':2,'no_detection':False,
                'detections':[{'grade':2,'detector_confidence':0.88}],
                'overlay_png_base64':'generated-v1-overlay','photo_saved':False}


@pytest.fixture(scope='module')
def servers():
    x,y=generated_inputs();model=make_xgboost_pipeline(('Full','A'));model.fit(x,y)
    prototype=QuestionnairePrototype(model,fit_support(x),{'final_model':False,'held_out_evaluated':False})
    items=[]
    for runtime,roi_runtime,roi_v1_runtime in (
        (None,None,None),
        (GeneratedRuntime(),GeneratedROIRuntime(),None),
        (GeneratedLocalUploadRuntime(),GeneratedLocalUploadROIRuntime(),GeneratedLocalUploadROIV1Runtime()),
    ):
        app=api.create_app(prototype,vision_runtime=runtime,
                           efficientnet_runtime=GeneratedLocalUploadRuntime() if isinstance(runtime,GeneratedLocalUploadRuntime) else None,
                           roi_v2_runtime=roi_runtime,
                           roi_v1_runtime=roi_v1_runtime,
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
    ports,prototype=servers
    port=ports[0]
    code,result=request(port,'/api/predict',{'profile':EXAMPLE_PROFILE})
    assert code==200 and result==prototype.predict(EXAMPLE_PROFILE)
    payload={'original':EXAMPLE_PROFILE,'model_id':prototype.model_id}
    code,changed=request(port,'/api/what-if',{**payload,'changes':{'OHQ870':7}})
    assert code==200 and changed==prototype.simulate(EXAMPLE_PROFILE,{'OHQ870':7},prototype.model_id)
    code,reset=request(port,'/api/reset',payload)
    assert code==200 and reset['scenario']==result and reset['is_reset']


@pytest.mark.parametrize('fault',['outcome','protected','version','nan','extra','duplicate','large','type'])
def test_api_validation_fail_closed(servers,fault):
    ports,prototype=servers
    port=ports[0]
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
    ports,_=servers
    port=ports[0]
    assert request(port,'/api/schema',headers={'Host':'evil.example'})[0]==403
    assert request(port,'/api/predict',{},headers={'Origin':'https://evil.example'})[0]==403
    assert request(port,'/api/predict',{},headers={'X-Component2-Demo':'0'})[0]==415
    assert request(port,'/api/schema')[0]==200
    assert b'app.js' in request(port,'/')[1]
    assert request(port,'/app.js')[0]==200
    script=request(port,'/app.js')[1]
    assert b'Run All Four Models' in script
    assert b'Doctor Review Mode' in script
    assert b'/api/vision/roi-v1-photo' in script
    assert b'Same 680-image OOF comparison' in script
    assert b'/api/vision/roi-photo' in script
    assert b'X-Component2-Photo-Consent' in script
    assert b'assumed sRGB' in script
    assert request(port,'/openapi.json')[1]['paths']['/api/predict']['post']['requestBody']['required']
    for path in ('/data/Test','/vision/unknown.png','/../AGENTS.md','/models/x.pt'):
        assert request(port,path)[0]==404


def test_photo_inactive_and_registered_synthetic_route(servers):
    ports,_=servers
    inactive,active=ports[:2]
    assert request(inactive,'/api/vision/runtime')[1]['ready'] is False
    assert request(inactive,'/api/vision/photo',raw=b'not decoded',headers={'Content-Type':'image/jpeg'})[0]==503
    assert request(active,'/api/vision/photo',raw=b'generated',headers={'Content-Type':'image/jpeg'})[1]['synthetic_only']
    assert request(active,'/api/vision/photo',raw=b'other',headers={'Content-Type':'image/jpeg'})[0]==422
    assert request(active,'/api/vision/photo',raw=b'generated')[0]==422


def test_efficientnet_photo_endpoint_permission_identity_and_failures(servers):
    from hashlib import sha256
    ports,_=servers
    assert request(ports[0],'/api/vision/efficientnet-runtime')[1]['ready'] is False
    assert request(ports[0],'/api/vision/efficientnet-photo',raw=b'generated')[0]==503
    port=ports[2]
    assert request(port,'/api/vision/efficientnet-runtime')[1]['ready'] is True
    headers={'Content-Type':'image/jpeg','X-Component2-Photo-Consent':'local-demo'}
    assert request(port,'/api/vision/efficientnet-photo',raw=b'generated',headers={'Content-Type':'image/jpeg'})[0]==403
    code,result=request(port,'/api/vision/efficientnet-photo',raw=b'generated',headers=headers)
    assert code==200 and result['input_sha256']==sha256(b'generated').hexdigest()
    assert result['photo_saved'] is False
    assert request(port,'/api/vision/efficientnet-photo',raw=b'bad',headers=headers)[0]==422
    assert request(port,'/api/vision/efficientnet-photo',raw=b'generated',headers={**headers,'Content-Type':'image/gif'})[0]==415
    # A failed candidate does not disable the existing baseline or questionnaire.
    assert request(port,'/api/vision/photo',raw=b'generated',headers=headers)[0]==200
    assert request(port,'/api/predict',{'profile':EXAMPLE_PROFILE})[0]==200


def test_roi_photo_runtime_is_separate_and_requires_registered_image(servers):
    ports,_=servers
    inactive,active=ports[:2]
    assert request(inactive,'/api/vision/roi-runtime')[1]['ready'] is False
    assert request(active,'/api/vision/roi-runtime')[1]['fold']==0
    assert request(inactive,'/api/vision/roi-photo',raw=b'not decoded',
                   headers={'Content-Type':'image/jpeg'})[0]==503
    code,result=request(active,'/api/vision/roi-photo',raw=b'generated',
                        headers={'Content-Type':'image/jpeg'})
    assert code==200
    assert result['image_mgi_grade']==3 and result['detections'][0]['grade']==3
    assert result['overlay_png_base64']=='generated-overlay'
    assert request(active,'/api/vision/roi-photo',raw=b'other',
                   headers={'Content-Type':'image/jpeg'})[0]==422


def test_roi_v1_upload_route_requires_consent_and_returns_a_separate_model_result(servers):
    ports,_=servers
    inactive,registered,active=ports
    assert request(inactive,'/api/vision/roi-v1-runtime')[1]['ready'] is False
    assert request(active,'/api/vision/roi-v1-runtime')[1]['ready'] is True
    headers={'Content-Type':'image/png','X-Component2-Photo-Consent':'local-demo'}
    assert request(active,'/api/vision/roi-v1-photo',raw=b'generated',
                   headers={'Content-Type':'image/png'})[0]==403
    assert request(active,'/api/vision/roi-v1-photo',raw=b'generated',headers=headers)[1]['model_family']=='roi_tooth_v1'
    assert request(registered,'/api/vision/roi-v1-photo',raw=b'generated',headers=headers)[0]==503


def test_aggregate_evidence_endpoint_is_separate_and_fail_closed(servers):
    ports,_=servers
    inactive,active=ports[:2]
    assert request(inactive,'/api/vision/evidence')[0]==503
    code,result=request(active,'/api/vision/evidence')
    assert code==200 and result=={'scope':'generated_aggregate_fixture','test_used':False}


def test_questionnaire_evidence_is_unavailable_or_matches_running_model(servers):
    ports,prototype=servers
    inactive,active=ports[:2]
    assert request(inactive,'/api/questionnaire/evidence')[0]==503
    code,result=request(active,'/api/questionnaire/evidence')
    assert code==200 and result=={'scope':'generated','model_id':prototype.model_id}


def test_local_user_upload_requires_consent_and_supports_image_formats(servers):
    ports,_=servers
    upload=ports[2]
    assert request(upload,'/api/vision/runtime')[1]['upload_mode']=='local_user_upload_demo'
    assert request(upload,'/api/vision/photo',raw=b'generated',
                   headers={'Content-Type':'image/jpeg'})[0]==403
    consent={'Content-Type':'image/png','X-Component2-Photo-Consent':'local-demo'}
    code,result=request(upload,'/api/vision/photo',raw=b'generated',headers=consent)
    assert code==200 and result['photo_saved'] is False
    code,result=request(upload,'/api/vision/roi-photo',raw=b'generated',headers=consent)
    assert code==200 and result['image_mgi_grade']==3
    assert request(upload,'/api/vision/photo',raw=b'generated',
                   headers={'Content-Type':'image/gif','X-Component2-Photo-Consent':'local-demo'})[0]==415


@pytest.mark.parametrize('route',['/api/vision/photo','/api/vision/roi-v1-photo','/api/vision/roi-photo'])
def test_three_upload_routes_report_source_byte_identity(servers,route):
    from hashlib import sha256
    ports,_=servers
    code,result=request(ports[2],route,raw=b'generated',headers={
        'Content-Type':'image/png','X-Component2-Photo-Consent':'local-demo'})
    assert code==200 and result['input_sha256']==sha256(b'generated').hexdigest()


def test_one_failed_model_does_not_disable_other_models_or_questionnaire(servers,monkeypatch):
    ports,_=servers
    def fail(*args):
        raise RuntimeError('synthetic failure')
    monkeypatch.setattr(GeneratedLocalUploadROIRuntime,'predict_upload',fail)
    headers={'Content-Type':'image/png','X-Component2-Photo-Consent':'local-demo'}
    assert request(ports[2],'/api/vision/roi-photo',raw=b'generated',headers=headers)==(
        500,{'error':'Prediction/explanation failed; no result returned'})
    for route in ('/api/vision/photo','/api/vision/roi-v1-photo'):
        assert request(ports[2],route,raw=b'generated',headers=headers)[0]==200
    assert request(ports[2],'/api/predict',{'profile':EXAMPLE_PROFILE})[0]==200


def test_optional_checkpoint_failure_stays_unavailable_without_fallback():
    def broken_loader():
        raise FileNotFoundError('private path must not leak')
    runtime=api.load_optional_vision('Generated model',broken_loader)
    status=runtime.status()
    assert status['ready'] is False and 'FileNotFoundError' in status['message']
    assert 'private path' not in str(status)
