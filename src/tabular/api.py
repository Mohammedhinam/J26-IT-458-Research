"""Loopback-only Component 2 FastAPI adapter; scientific functions are reused.

Run: .venv/bin/python -B -m src.tabular.api
No dataset loading, training, model selection or photo runtime activation.
"""
import argparse
import json
from pathlib import Path
import threading
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict, ValidationError
from starlette.concurrency import run_in_threadpool

from . import local_demo as local
from .questionnaire_explain import FEATURES, FEATURE_LABELS, CAT_CODES, EXAMPLE_PROFILE, NOTICE

UI_ROOT=Path(__file__).with_name('ui')


class PredictBody(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    profile: dict


class ScenarioBody(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    original: dict
    changes: dict
    model_id: str


class ResetBody(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    original: dict
    model_id: str


def create_app(prototype,vision=None,assets=None,vision_runtime=None,vision_evidence=None,questionnaire_evidence=None):
    app=FastAPI(title='Component 2 development demonstration',version='2.0',docs_url=None,redoc_url=None)
    lock=threading.Lock(); assets={} if assets is None else dict(assets)
    def execute(function,*args):
        with lock: return function(*args)

    @app.middleware('http')
    async def local_boundary(request,call_next):
        host=request.headers.get('host','')
        try:
            parsed=urlsplit('http://'+host)
            valid=parsed.hostname in ('localhost','127.0.0.1') and not parsed.username and parsed.path==''
        except ValueError: valid=False
        if not valid: return JSONResponse({'error':'Loopback host required'},403)
        if request.method=='POST':
            origin=request.headers.get('origin')
            if origin is not None and origin!='http://'+host:
                return JSONResponse({'error':'Same-origin request required'},403)
            if request.headers.get('x-component2-demo')!='1':
                return JSONResponse({'error':'Use the local demonstration interface'},415)
        response=await call_next(request)
        response.headers.update({'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
          'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'"})
        return response

    async def bounded_body(request,maximum,kind):
        if request.headers.get('content-type','').split(';')[0]!=kind:
            raise ValueError('Unexpected Content-Type')
        content=bytearray()
        async for chunk in request.stream():
            if len(content)+len(chunk)>maximum: raise ValueError('Request size exceeds limit')
            content.extend(chunk)
        if not content: raise ValueError('Empty request')
        return bytes(content)

    async def parsed_body(request,model):
        raw=await bounded_body(request,8192,'application/json')
        def invalid(value): raise ValueError('Non-finite JSON is forbidden')
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result: raise ValueError('Duplicate JSON fields')
                result[key]=value
            return result
        return model.model_validate(json.loads(raw,parse_constant=invalid,object_pairs_hook=unique))

    @app.exception_handler(ValueError)
    async def invalid_request(request,error):
        return JSONResponse({'error':str(error)},422)

    @app.exception_handler(ValidationError)
    async def invalid_schema(request,error):
        # Do not echo input values or private profiles in validation errors.
        return JSONResponse({'error':'Invalid request fields or types'},422)

    @app.exception_handler(Exception)
    async def unavailable(request,error):
        return JSONResponse({'error':'Prediction/explanation failed; no result returned'},500)

    @app.get('/',response_class=HTMLResponse)
    def page(): return (UI_ROOT/'index.html').read_text()

    @app.get('/app.js')
    def script(): return Response((UI_ROOT/'app.js').read_bytes(),media_type='text/javascript')

    @app.get('/style.css')
    def style(): return Response((UI_ROOT/'style.css').read_bytes(),media_type='text/css')

    @app.get('/favicon.ico',status_code=204)
    def favicon(): return Response(status_code=204)

    @app.get('/api/schema')
    def schema():
        return {'notice':NOTICE,'model_id':prototype.model_id,'example':EXAMPLE_PROFILE,
                'fields':[{'key':f,'label':FEATURE_LABELS[f],
                'options':list(zip(map(str,CAT_CODES[f]),local.OPTIONS[f])) if f in CAT_CODES else None} for f in FEATURES]}

    @app.get('/api/questionnaire/evidence')
    def questionnaire_results():
        # Aggregate report only: this route cannot trigger a Test evaluation.
        if questionnaire_evidence is None or questionnaire_evidence.get('model_id') != prototype.model_id:
            return JSONResponse({'error':'Matching frozen questionnaire evidence unavailable'},503)
        return questionnaire_evidence

    @app.post('/api/predict',summary='Previous-treatment probability and log-odds TreeSHAP')
    async def predict(request:Request):
        body=await parsed_body(request,PredictBody)
        return await run_in_threadpool(execute,prototype.predict,body.profile)

    @app.post('/api/what-if',summary='Constrained model sensitivity; no causal interpretation')
    async def scenario(request:Request):
        body=await parsed_body(request,ScenarioBody)
        return await run_in_threadpool(execute,prototype.simulate,body.original,body.changes,body.model_id)

    @app.post('/api/reset',summary='Reproduce the unchanged original profile')
    async def reset(request:Request):
        body=await parsed_body(request,ResetBody)
        return await run_in_threadpool(execute,prototype.reset,body.original,body.model_id)

    @app.get('/api/vision')
    def saved(): return vision if vision is not None else JSONResponse({'error':'Saved examples unavailable'},503)

    @app.get('/api/vision/evidence')
    def evidence():
        return vision_evidence if vision_evidence is not None else JSONResponse({'error':'Verified aggregate evidence unavailable'},503)

    @app.get('/vision/{name}')
    def view(name:str):
        if name not in assets: return JSONResponse({'error':'Unknown saved view'},404)
        return Response(assets[name],media_type='image/png')

    @app.get('/api/vision/runtime')
    def status():
        return vision_runtime.status() if vision_runtime else {'ready':False,'synthetic_only':False,
            'message':'New-photo runtime is not enabled. Saved pilot examples remain available.'}

    @app.post('/api/vision/photo')
    async def photo(request:Request):
        if not vision_runtime or not vision_runtime.status().get('ready'):
            return JSONResponse({'error':'New-photo runtime inactive; no image processed'},503)
        payload=await bounded_body(request,8*1024*1024,'image/jpeg')
        return await run_in_threadpool(execute,vision_runtime.explain,payload)

    # Machine-readable request contracts, without a CDN-dependent Swagger page.
    original_openapi=app.openapi
    def openapi():
        result=original_openapi()
        for route,model in (('/api/predict',PredictBody),('/api/what-if',ScenarioBody),('/api/reset',ResetBody)):
            result['paths'][route]['post']['requestBody']={'required':True,'content':{
                'application/json':{'schema':model.model_json_schema()}}}
        return result
    app.openapi=openapi
    return app


def main():
    import uvicorn
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8766)
    args=parser.parse_args()
    prototype=local.load_verified_prototype(); vision,assets=local.load_vision_assets()
    from src.vision.vision_evidence import load_evidence
    from .questionnaire_evidence import load_evidence as load_questionnaire_evidence
    app=create_app(prototype,vision,assets,vision_evidence=load_evidence(),
                   questionnaire_evidence=load_questionnaire_evidence(prototype.model_id))
    print(f'Component 2 React/FastAPI demo: http://127.0.0.1:{args.port}',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=args.port,access_log=False,log_level='warning')


if __name__=='__main__': main()
