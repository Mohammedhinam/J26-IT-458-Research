"""Loopback-only Component 2 FastAPI adapter; scientific functions are reused.

Run: .venv/bin/python -B -m src.tabular.api
No dataset loading, training or model selection. Photo runtime is explicit opt-in.
"""
import argparse
from hashlib import sha256
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


class UnavailableVisionRuntime:
    """A failed optional model must not take down the other demo branches."""
    synthetic_only=False

    def __init__(self, label, reason):
        self.label=label
        self.reason=reason

    def status(self):
        return {'ready':False,'message':f'{self.label} unavailable ({self.reason}); no fallback predictions.',
                'upload_mode':'local_user_upload_demo','synthetic_only':False}


def load_optional_vision(label, loader, *args, **kwargs):
    try:
        return loader(*args, **kwargs)
    except Exception as error:
        # Keep input paths and deserialization details out of browser responses.
        print(f'{label} unavailable: {type(error).__name__}',flush=True)
        return UnavailableVisionRuntime(label,type(error).__name__)


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


def create_app(prototype,vision=None,assets=None,vision_runtime=None,vision_evidence=None,
               questionnaire_evidence=None,roi_v2_runtime=None,roi_v1_runtime=None,
               efficientnet_runtime=None):
    app=FastAPI(title='Component 2 development demonstration',version='2.0',docs_url=None,redoc_url=None)
    lock=threading.Lock(); assets={} if assets is None else dict(assets)
    def execute(function,*args):
        with lock: return function(*args)

    def photo_result(function,payload,*args):
        # Prove byte identity across independent endpoints without logging the photo.
        result=execute(function,payload,*args)
        return {**result,'input_sha256':sha256(payload).hexdigest()}

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
          'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; frame-ancestors 'none'"})
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
        runtime_status=vision_runtime.status()
        upload_mode=runtime_status.get('upload_mode')
        if upload_mode=='local_user_upload_demo':
            if request.headers.get('x-component2-photo-consent')!='local-demo':
                return JSONResponse({'error':'Confirm photo permission and research-demo limitations first'},403)
            content_type=request.headers.get('content-type','').split(';')[0]
            allowed={'image/jpeg','image/png','image/webp'}
            if content_type not in allowed:
                return JSONResponse({'error':'Use a JPEG, PNG or WebP photo'},415)
        else:
            content_type='image/jpeg'
        payload=await bounded_body(request,8*1024*1024,content_type)
        try:
            if upload_mode=='local_user_upload_demo':
                return await run_in_threadpool(photo_result,vision_runtime.explain_upload,payload,content_type)
            return await run_in_threadpool(photo_result,vision_runtime.explain,payload)
        except OSError:
            return JSONResponse({'error':'Invalid or unsupported photo payload'},422)

    @app.get('/api/vision/efficientnet-runtime')
    def efficientnet_status():
        if efficientnet_runtime is None:
            return {'ready':False,'message':'EfficientNet candidate runtime is not enabled.'}
        return efficientnet_runtime.status()

    @app.post('/api/vision/efficientnet-photo')
    async def efficientnet_photo(request:Request):
        if not efficientnet_runtime or not efficientnet_runtime.status().get('ready'):
            return JSONResponse({'error':'EfficientNet runtime inactive; no image processed'},503)
        if request.headers.get('x-component2-photo-consent')!='local-demo':
            return JSONResponse({'error':'Confirm photo permission and research-demo limitations first'},403)
        content_type=request.headers.get('content-type','').split(';')[0]
        if content_type not in {'image/jpeg','image/png','image/webp'}:
            return JSONResponse({'error':'Use a JPEG, PNG or WebP photo'},415)
        payload=await bounded_body(request,8*1024*1024,content_type)
        try:
            return await run_in_threadpool(photo_result,efficientnet_runtime.explain_upload,payload,content_type)
        except OSError:
            return JSONResponse({'error':'Invalid or unsupported photo payload'},422)

    @app.get('/api/vision/roi-runtime')
    def roi_runtime_status():
        if roi_v2_runtime is None:
            return {'ready':False,'message':'The experimental ROI model is not enabled.'}
        return roi_v2_runtime.status()

    @app.get('/api/vision/roi-v1-runtime')
    def roi_v1_runtime_status():
        if roi_v1_runtime is None:
            return {'ready':False,'message':'The ROI v1 model is not enabled.'}
        return roi_v1_runtime.status()

    @app.post('/api/vision/roi-photo')
    async def roi_photo(request:Request):
        if not roi_v2_runtime or not roi_v2_runtime.status().get('ready'):
            return JSONResponse({'error':'Experimental ROI photo runtime inactive; no image processed'},503)
        roi_status=roi_v2_runtime.status()
        upload_mode=roi_status.get('upload_mode')
        if upload_mode=='local_user_upload_demo':
            if request.headers.get('x-component2-photo-consent')!='local-demo':
                return JSONResponse({'error':'Confirm photo permission and research-demo limitations first'},403)
            content_type=request.headers.get('content-type','').split(';')[0]
            if content_type not in {'image/jpeg','image/png','image/webp'}:
                return JSONResponse({'error':'Use a JPEG, PNG or WebP photo'},415)
        else:
            content_type='image/jpeg'
        payload=await bounded_body(request,8*1024*1024,content_type)
        try:
            if upload_mode=='local_user_upload_demo':
                return await run_in_threadpool(photo_result,roi_v2_runtime.predict_upload,payload,content_type)
            return await run_in_threadpool(photo_result,roi_v2_runtime.predict,payload)
        except OSError:
            return JSONResponse({'error':'Invalid or unsupported photo payload'},422)

    @app.post('/api/vision/roi-v1-photo')
    async def roi_v1_photo(request:Request):
        if not roi_v1_runtime or not roi_v1_runtime.status().get('ready'):
            return JSONResponse({'error':'Experimental ROI v1 photo runtime inactive; no image processed'},503)
        if request.headers.get('x-component2-photo-consent')!='local-demo':
            return JSONResponse({'error':'Confirm photo permission and research-demo limitations first'},403)
        content_type=request.headers.get('content-type','').split(';')[0]
        if content_type not in {'image/jpeg','image/png','image/webp'}:
            return JSONResponse({'error':'Use a JPEG, PNG or WebP photo'},415)
        payload=await bounded_body(request,8*1024*1024,content_type)
        try:
            return await run_in_threadpool(photo_result,roi_v1_runtime.predict_upload,payload,content_type)
        except OSError:
            return JSONResponse({'error':'Invalid or unsupported photo payload'},422)

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
    parser.add_argument('--vision-checkpoint',type=Path)
    parser.add_argument('--efficientnet-checkpoint',type=Path,
                        help='Pinned fold-0 EfficientNet main candidate, local photo mode only')
    parser.add_argument('--vision-registration',type=Path)
    parser.add_argument('--vision-registration-sha256')
    parser.add_argument('--local-photo-uploads',action='store_true',
                        help='Allow presenter-selected, temporary photo inference on loopback only')
    parser.add_argument('--roi-v2-return-zip',type=Path)
    parser.add_argument('--roi-v2-device')
    parser.add_argument('--roi-v1-return-zip',type=Path)
    parser.add_argument('--roi-v1-device')
    args=parser.parse_args()
    supplied=(args.vision_checkpoint,args.vision_registration,args.vision_registration_sha256)
    if (args.vision_registration is None) != (args.vision_registration_sha256 is None):
        parser.error('--vision-registration and --vision-registration-sha256 must be supplied together')
    if (not args.local_photo_uploads and any(value is not None for value in supplied)
            and not all(value is not None for value in supplied)):
        parser.error('All three --vision-* bindings are required together')
    runtime=None
    efficientnet_runtime=None
    if args.efficientnet_checkpoint is not None:
        if not args.local_photo_uploads:
            parser.error('--efficientnet-checkpoint requires --local-photo-uploads')
        from src.vision.efficientnet_live import load_runtime as load_efficientnet
        efficientnet_runtime=load_optional_vision('EfficientNet-B0',load_efficientnet,args.efficientnet_checkpoint)
    if args.local_photo_uploads:
        if args.vision_registration is not None or args.vision_registration_sha256 is not None:
            parser.error('--local-photo-uploads and a source registration are separate runtime modes')
        if args.vision_checkpoint is None:
            parser.error('--local-photo-uploads requires --vision-checkpoint')
        from src.vision.local_photo_upload_demo import load_runtime
        runtime=load_optional_vision('ResNet50 v3',load_runtime,args.vision_checkpoint)
    elif args.vision_registration is not None:
        from src.vision.live_photo_demo import build_runtime
        runtime=build_runtime(*supplied)
    if args.roi_v2_return_zip is not None and runtime is None:
        parser.error('--roi-v2-return-zip requires a registered or --local-photo-uploads Vision runtime')
    if args.roi_v2_device is not None and args.roi_v2_return_zip is None:
        parser.error('--roi-v2-device requires --roi-v2-return-zip')
    if args.roi_v1_return_zip is not None and not args.local_photo_uploads:
        parser.error('--roi-v1-return-zip requires --local-photo-uploads')
    if args.roi_v1_device is not None and args.roi_v1_return_zip is None:
        parser.error('--roi-v1-device requires --roi-v1-return-zip')
    roi_runtime=None
    if args.roi_v2_return_zip is not None:
        from src.vision.roi_ordinal_v2_live import build_runtime as build_roi_runtime
        photo_scope=runtime
        if args.local_photo_uploads:
            # Upload permission is independent of whether the ResNet checkpoint loaded.
            from types import SimpleNamespace
            photo_scope=SimpleNamespace(synthetic_only=False,status=lambda:{
                'ready':True,'upload_mode':'local_user_upload_demo'})
        roi_runtime=load_optional_vision('ROI v2 CORAL',build_roi_runtime,
            args.roi_v2_return_zip,photo_scope,device=args.roi_v2_device)
    roi_v1_runtime=None
    if args.roi_v1_return_zip is not None:
        from src.vision.roi_tooth_v1_live import build_runtime as build_roi_v1_runtime
        roi_v1_runtime=load_optional_vision('ROI v1',build_roi_v1_runtime,
            args.roi_v1_return_zip,device=args.roi_v1_device)
    prototype=local.load_verified_prototype(); vision,assets=local.load_vision_assets()
    from src.vision.vision_evidence import load_evidence
    from .questionnaire_evidence import load_evidence as load_questionnaire_evidence
    app=create_app(prototype,vision,assets,vision_runtime=runtime,vision_evidence=load_evidence(),
                   questionnaire_evidence=load_questionnaire_evidence(prototype.model_id),
                   roi_v2_runtime=roi_runtime,roi_v1_runtime=roi_v1_runtime,
                   efficientnet_runtime=efficientnet_runtime)
    print(f'Component 2 React/FastAPI demo: http://127.0.0.1:{args.port}',flush=True)
    uvicorn.run(app,host='127.0.0.1',port=args.port,access_log=False,log_level='warning')


if __name__=='__main__': main()
