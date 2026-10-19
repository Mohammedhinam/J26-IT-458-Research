/* Browser verification against a running local API. No model training or Test data. */
const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const out=process.env.PP1_EVIDENCE_DIR||path.join(root,'data/vision/doctor_demo_20261018_v1');
const base=process.env.PP1_DEMO_URL||'http://127.0.0.1:8771';
const photo=process.env.PP1_PERMITTED_PHOTO;
if(!photo)throw Error('Set PP1_PERMITTED_PHOTO to a permitted non-study JPG/PNG.');
const sourceHash=crypto.createHash('sha256').update(fs.readFileSync(photo)).digest('hex');
const routes=['/api/vision/photo','/api/vision/roi-v1-photo','/api/vision/roi-photo'];
const report={passed:[],failed:[],real_outputs:[],synthetic_fault_checks:true};
const check=(ok,name)=>{if(!ok){report.failed.push(name);throw Error(name);}report.passed.push(name);};
const wait=async(page,selector)=>page.waitForFunction(selector,null,{timeout:60000});
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const context=await browser.newContext({viewport:{width:1512,height:982},acceptDownloads:true});
 const page=await context.newPage();const errors=[],external=[];
 page.on('pageerror',error=>errors.push(error.message));
 page.on('request',request=>{const url=request.url();if(/^https?:/.test(url)&&new URL(url).origin!==base)external.push(url);});
 // Read cloned responses inside the page, avoiding CDP inspector cache eviction.
 await page.addInitScript(()=>{window.inferenceEvidence=[];const nativeFetch=window.fetch;window.fetch=async(...args)=>{
   const response=await nativeFetch(...args);const url=String(args[0]);
   if(['/api/vision/photo','/api/vision/roi-v1-photo','/api/vision/roi-photo'].includes(url)){
     const data=await response.clone().json();window.inferenceEvidence.push({url,status:response.status,hash:data.input_sha256,
       grade:data.predicted_grade??data.image_mgi_grade,rois:data.detections?.length,cam:data.explanation_status,
       photo_saved:data.photo_saved,checkpoint:data.checkpoint_sha256??data.classifier_checkpoint_sha256,
       detector:data.detector_checkpoint_sha256,probabilities:data.probabilities});
   }return response;
 };});
 try{
  await page.goto(base);
  await page.getByRole('button',{name:'Questionnaire · live explanation',exact:true}).click();
  await page.getByRole('button',{name:'Explain this profile',exact:true}).click();
  await page.getByTestId('probability').waitFor();const probability=await page.getByTestId('probability').innerText();
  check(/\d/.test(probability),'Questionnaire live probability and SHAP render');
  await page.getByLabel('Scenario cleaning days',{exact:true}).fill('7');
  await page.getByRole('button',{name:'Compare scenario',exact:true}).click();await page.getByTestId('scenario').waitFor();
  check((await page.getByTestId('scenario').innerText()).includes('Scenario'),'Questionnaire what-if renders');
  await page.getByRole('button',{name:'Reset scenario',exact:true}).click();
  await page.getByText('Reset: original prediction restored exactly.',{exact:true}).waitFor();
  check(await page.getByTestId('probability').innerText()===probability,'Questionnaire reset restores original probability');
  await page.getByRole('button',{name:'Vision · exploratory evidence',exact:true}).click();
  await page.getByLabel('Intraoral photo',{exact:true}).setInputFiles(photo);
  const run=page.getByRole('button',{name:'Run All Three Models',exact:true});
  check(await run.isDisabled(),'Consent and doctor assessment gate Run All');
  await page.getByLabel('Photo permission',{exact:true}).check();
  check(await run.isDisabled(),'Consent alone does not bypass doctor assessment');
  await page.getByLabel('Independent MGI assessment',{exact:true}).selectOption('unassessable');
  await page.getByRole('button',{name:'Record independent assessment',exact:true}).click();
  check(await page.getByLabel('Independent MGI assessment',{exact:true}).isDisabled(),'Independent assessment locks before reveal');
  await page.getByRole('button',{name:'Developer Demo Mode',exact:true}).click();
  await page.waitForFunction(()=>Array.from(document.querySelectorAll('button')).some(b=>b.textContent==='Run All Three Models'&&!b.disabled));
  check((await page.getByTestId('doctor-demo').innerText()).includes('not clinically reviewed'),'Developer mode clearly marked');
  await run.click();
  await wait(page,()=>Array.from(document.querySelectorAll('.model-status')).every(e=>e.textContent==='Success'));
  report.real_outputs=await page.evaluate(()=>window.inferenceEvidence);
  check(report.real_outputs.length===3&&report.real_outputs.every(x=>x.status===200),'Three real checkpoint API responses succeed');
  check(report.real_outputs.every(x=>x.hash===sourceHash),'All real endpoints verify identical source bytes');
  check(report.real_outputs.every(x=>x.photo_saved===false),'Real endpoints report no permanent photo storage');
  check(await page.getByTestId('model-v1').getByText('Not provided',{exact:true}).count()>0,'v1 does not fabricate crop probabilities');
  check(await page.getByTestId('model-v2').getByText('All per-crop grade probabilities shown above',{exact:false}).count()===1,'CORAL full per-crop probabilities available');
  check(await page.locator('.model-grid img').count()===5,'Real Grad-CAM and both box overlays render');
  check(await page.locator('.doctor-demo img').evaluateAll(imgs=>imgs.every(i=>i.complete&&i.naturalWidth>0)),'Original blob preview and all output images load');
  const columns=await page.locator('.model-card').evaluateAll(cards=>cards.map(c=>Math.round(c.getBoundingClientRect().x)));
  check(columns[0]<columns[1]&&columns[1]<columns[2],'Three model cards display side by side on desktop');
  await page.getByRole('group',{name:'resnet agreement',exact:true}).getByRole('button',{name:'Uncertain',exact:true}).click();
  await page.getByLabel('resnet reason',{exact:true}).selectOption('Questionable attention');
  await page.getByLabel('resnet notes',{exact:true}).fill('=Software test only; no clinician assessment');
  await page.getByLabel('v1 clinician grade',{exact:true}).selectOption('0');
  let pending=page.waitForEvent('download');await page.getByRole('button',{name:'Export Feedback',exact:true}).click();
  const jsonDownload=await pending;await jsonDownload.saveAs(path.join(out,'feedback_smoke.json'));
  const feedback=JSON.parse(fs.readFileSync(path.join(out,'feedback_smoke.json'),'utf8'));
  check(feedback.clinically_reviewed===false&&feedback.independent_assessment===null&&feedback.automatic_retraining===false,'Developer export keeps review and retraining status honest');
  check(feedback.models[1].reviewer_grade===0&&feedback.models[1].predicted_mgi_grade===report.real_outputs[1].grade,'Feedback grade 0 stays separate from prediction');
  const exported=JSON.stringify(feedback);
  check(!/input_sha256|views_png|base64|filename|patient_id/.test(exported)&&!exported.includes(path.basename(photo)),'JSON allowlist excludes photo bytes, photo hash and identifiers');
  await page.getByLabel('Feedback export format',{exact:true}).selectOption('csv');
  pending=page.waitForEvent('download');await page.getByRole('button',{name:'Export Feedback',exact:true}).click();
  await(await pending).saveAs(path.join(out,'feedback_smoke.csv'));
  check(fs.readFileSync(path.join(out,'feedback_smoke.csv'),'utf8').includes("'=Software"),'CSV quotes and neutralises spreadsheet formulas');
  const heights=await page.locator('.model-card').evaluateAll(cards=>cards.map(c=>Math.round(c.getBoundingClientRect().height)));
  check(Math.max(...heights)-Math.min(...heights)<=1,'Balanced model cards have equal desktop heights');
  await page.getByRole('button',{name:'Results & Feedback',exact:true}).click();
  await page.getByRole('heading',{name:/Developer evaluation & observations/}).waitFor();
  check(await page.locator('#doctor-feedback .feedback-card').count()===3,'Sidebar links to three separate feedback cards');
  await page.getByRole('button',{name:'Model Comparison',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('model-comparison').open);
  check(await page.locator('#model-comparison').getAttribute('open')!==null,'Model Comparison navigation expands actual evidence');
  await page.getByRole('button',{name:'About the project',exact:true}).click();
  await page.waitForFunction(()=>document.getElementById('about-project').open);
  check(await page.locator('#about-project').getAttribute('open')!==null,'About navigation opens project information');
  await page.locator('#model-comparison').evaluate(e=>e.open=false);await page.locator('#about-project').evaluate(e=>e.open=false);
  await page.getByRole('button',{name:'Vision · exploratory evidence',exact:true}).click();
  await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
  await page.waitForFunction(()=>window.scrollY<2,null,{timeout:5000});
  await page.screenshot({path:path.join(out,'desktop_real_outputs.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'Mobile page has no horizontal overflow');
  await page.screenshot({path:path.join(out,'mobile_real_outputs.png'),fullPage:true});
  await page.setViewportSize({width:1512,height:982});
  // Fault tests below use explicitly synthetic responses, never as model evidence.
  const pixel='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
  function fixture(endpoint){return endpoint===routes[0]?{synthetic_only:true,predicted_grade:2,explained_grade:2,mgi_grades:[1,2,3,4],probabilities:[.1,.7,.1,.1],views_png_base64:{original:pixel,heatmap:pixel,overlay:pixel},explanation_status:'no_spatial_contrast',input_sha256:sourceHash}:{synthetic_only:true,image_mgi_grade:null,detections:[],no_detection:true,fold:0,overlay_png_base64:pixel,input_sha256:sourceHash};}
  let fault='v1';let delayedResolve;let delayedSeen=false;
  await page.route('**/api/vision/*photo',async route=>{const endpoint=new URL(route.request().url()).pathname;
    if(fault==='delay'&&endpoint===routes[0]){delayedSeen=true;await new Promise(resolve=>delayedResolve=resolve);}
    if(fault==='v1'&&endpoint===routes[1])return route.fulfill({status:500,json:{error:'SYNTHETIC browser failure'}});
    const result=fixture(endpoint);if(fault==='hash'&&endpoint===routes[1])result.input_sha256='wrong';
    try{await route.fulfill({json:result});}catch(e){if(fault!=='delay')throw e;}
  });
  await run.click();await wait(page,()=>document.querySelector('[data-testid="model-v2"] .model-status').textContent==='Success');
  check(await page.locator('.model-status').allTextContents().then(x=>x.join(',')==='Success,Failed,Success'),'One model failure preserves both successful results');
  check((await page.getByTestId('model-v2').innerText()).includes('No tooth ROI detected'),'No detections return no image grade');
  check((await page.getByTestId('model-resnet').innerText()).includes('limited or absent usable spatial signal'),'Flat CAM is explicitly qualified');
  fault='hash';await run.click();await wait(page,()=>document.querySelector('[data-testid="model-v2"] .model-status').textContent==='Success');
  check((await page.getByTestId('model-v1').innerText()).includes('Input identity could not be verified'),'Wrong-photo identity rejects only that model');
  fault='delay';await run.click();while(!delayedSeen)await page.waitForTimeout(20);
  await page.getByRole('button',{name:'Reset case',exact:true}).click();delayedResolve();await page.waitForTimeout(300);
  check((await page.locator('.model-status').allTextContents()).every(x=>x==='Not run'),'Reset ignores late in-flight response');
  check(await page.getByRole('button',{name:'Export Feedback',exact:true}).isDisabled(),'Reset clears exportable results');
  await page.getByRole('button',{name:'Doctor Review Mode',exact:true}).click();
  await page.getByLabel('Intraoral photo',{exact:true}).setInputFiles(photo);await page.getByLabel('Photo permission',{exact:true}).check();
  await page.getByLabel('Independent MGI assessment',{exact:true}).selectOption('uncertain');await page.getByRole('button',{name:'Record independent assessment',exact:true}).click();
  fault='none';await run.click();await wait(page,()=>Array.from(document.querySelectorAll('.model-status')).every(e=>e.textContent==='Success'));
  await page.getByLabel('Feedback export format',{exact:true}).selectOption('json');
  pending=page.waitForEvent('download');await page.getByRole('button',{name:'Export Feedback',exact:true}).click();await(await pending).saveAs(path.join(out,'doctor_mode_synthetic_feedback.json'));
  const doctor=JSON.parse(fs.readFileSync(path.join(out,'doctor_mode_synthetic_feedback.json'),'utf8'));
  check(doctor.review_mode==='doctor'&&doctor.independent_assessment==='uncertain'&&doctor.models.every(m=>m.reviewer_role==='clinician'),'Doctor-mode export retains pre-reveal assessment');
  // Changing file invalidates assessment, feedback, consent and successful results.
  await page.getByLabel('Intraoral photo',{exact:true}).setInputFiles({name:'different-case.jpg',mimeType:'image/jpeg',buffer:fs.readFileSync(photo)});
  check(await run.isDisabled()&&(await page.locator('.model-status').allTextContents()).every(x=>x==='Not run'),'Changing photo clears all case-bound state');
  await page.getByLabel('Intraoral photo',{exact:true}).setInputFiles({name:'bad.webp',mimeType:'image/webp',buffer:Buffer.from('synthetic')});
  check((await page.getByTestId('doctor-demo').innerText()).includes('Choose a nonempty JPG or PNG'),'Unsupported input rejected');
  await page.locator('.upload-drop').evaluate((element,bytes)=>{const transfer=new DataTransfer();transfer.items.add(new File([new Uint8Array(bytes)],'drop-case.jpg',{type:'image/jpeg'}));element.dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:transfer}));},Array.from(fs.readFileSync(photo)));
  check(await page.locator('.source-preview img').count()===1&&await run.isDisabled(),'Drag-and-drop accepts one photo and requires fresh consent');
  check(await page.evaluate(()=>localStorage.length===0&&sessionStorage.length===0),'No localStorage or sessionStorage persistence');
  check(external.length===0,'No external browser transmissions');
  check(errors.length===0,'No JavaScript page errors');
 }catch(error){report.error=error.stack;process.exitCode=1;await page.screenshot({path:path.join(out,'browser_failure.png'),fullPage:true});}
 finally{report.pass_count=report.passed.length;report.fail_count=report.failed.length+(report.error&&!report.failed.length?1:0);fs.writeFileSync(path.join(out,'browser_verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();}
})();
