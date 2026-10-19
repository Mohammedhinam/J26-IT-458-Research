import React, {useEffect,useRef,useState} from 'react';
import Icon from './Icons';

const MODELS=[
  {id:'efficientnet',letter:'A',name:'EfficientNet-B0',whole:true,detail:'Main candidate · Grad-CAM · fold 00',status:'/api/vision/efficientnet-runtime',endpoint:'/api/vision/efficientnet-photo'},
  {id:'resnet',letter:'B',name:'ResNet50 v3',whole:true,detail:'Baseline comparison · Grad-CAM',status:'/api/vision/runtime',endpoint:'/api/vision/photo'},
  {id:'v1',letter:'C',name:'YOLO ROI v1 + ResNet18',detail:'Tooth ROI · weighted cross-entropy',status:'/api/vision/roi-v1-runtime',endpoint:'/api/vision/roi-v1-photo'},
  {id:'v2',letter:'D',name:'YOLO ROI v2 CORAL',detail:'Tooth ROI · ordinal crop classifier',status:'/api/vision/roi-runtime',endpoint:'/api/vision/roi-photo'},
];
const emptyRuns=()=>Object.fromEntries(MODELS.map(m=>[m.id,{status:'Not run'}]));
const score=value=>`${(100*value).toFixed(1)}%`;
const png=value=>`data:image/png;base64,${value}`;
const gradeOptions=<><option value="">Choose an assessment</option>{[0,1,2,3,4].map(g=><option key={g} value={String(g)}>MGI {g}</option>)}<option value="uncertain">Uncertain</option><option value="unassessable">Cannot assess from this photo</option></>;

function ModelDetails({result}){
  const hashes=[['Checkpoint',result.checkpoint_sha256],['Detector',result.detector_checkpoint_sha256],['Crop classifier',result.classifier_checkpoint_sha256]];
  return <details><summary>Checkpoint & processing details</summary>
    <p>{result.fold===undefined?'ResNet50 B1 v3 · historical development pilot':`Cross-validation fold ${String(result.fold).padStart(2,'0')} · not an all-development refit`}</p>
    {result.model_name&&<p>{result.model_name} · {result.training_arm} · CAM layer {result.cam_target_layer}</p>}
    {result.evaluation&&<p>Neural last-block experiment: {(100*result.evaluation.accuracy).toFixed(2)}% accuracy, Macro-F1 {result.evaluation.macro_f1.toFixed(4)} on 680-image OOF. Separate from the 52.21% frozen-features + Logistic experiment. Main candidate is a proposal role, not an accuracy winner.</p>}
    {result.device&&<p>Device: {result.device}</p>}
    {hashes.filter(([,v])=>v).map(([label,value])=><p className="hash" key={label}>{label} SHA-256: {value}</p>)}
    <p>{result.input_colour_policy}</p><p>Photo is not permanently saved. Labels are provisional.</p>
  </details>;
}
function ModelOutput({model,result}){
  const grade=model.whole?result.predicted_grade:result.image_mgi_grade;
  return <div className="model-content">
    <div className="prediction-overview"><div><span className="metric-title">{model.whole?'Predicted image MGI':'Maximum detected crop MGI'}</span><div className="grade-value"><strong className={`grade-${grade}`}>{grade??'—'}</strong><span className="grade-chip">{grade==null?'No grade available':`MGI ${grade}`}</span></div></div>
      <div className="metric-box">{model.whole?<><span>Top-class score</span><strong>{score(Math.max(...result.probabilities))}</strong><div className="mini-track"><i style={{width:score(Math.max(...result.probabilities))}}/></div><small>Uncalibrated</small></>:<><span>Detected tooth ROIs</span><strong>{result.detections.length}</strong><small>Fold {String(result.fold).padStart(2,'0')}</small></>}</div>
    </div>
    {model.whole?<>
      <h4>Class scores <span>MGI 1–4</span></h4>
      <div className="score-list">{result.probabilities.map((p,i)=><div key={i}><span>Grade {result.mgi_grades[i]}</span><div className="probability-track"><i className={`score-grade-${result.mgi_grades[i]}`} style={{width:score(p)}}/></div><strong>{score(p)}</strong></div>)}</div>
      <h4>Grad-CAM visualisation</h4><div className="model-views">{['original','heatmap','overlay'].map(view=><figure key={view}><img src={png(result.views_png_base64[view])} alt={`${model.name} ${view}`}/><figcaption>{view==='original'?'Original preview':view==='heatmap'?'Heatmap':'Overlay'}</figcaption></figure>)}</div>
      <p className="attention-warning">Relative model attention, not validated disease localisation. Teeth, lips or other regions may be highlighted.</p>
      <p className="muted cam-status">Explains MGI {result.explained_grade} · status: <strong>{result.explanation_status}</strong>. MGI 0 is unsupported by this four-output model.</p>
      {result.explanation_status!=='ok'&&<p className="attention-warning" role="status">The heatmap has limited or absent usable spatial signal; do not interpret it as localisation.</p>}
      <p className="muted">Uncalibrated scores are not clinical probabilities. Heatmap intensity is relative within this photo, not severity or confidence.</p>
    </>:<>
      <h4>Detected tooth / ROI regions</h4>
      <figure className="roi-figure"><img className="roi-preview" src={png(result.overlay_png_base64)} alt={`${model.name} predicted tooth ROI boxes`}/><figcaption>Predicted boxes · numbers match the ROI table.</figcaption></figure>
      {result.no_detection&&<p className="attention-warning">No tooth ROI detected; no image-level grade is returned.</p>}
      <h4>Per-ROI predictions{model.id==='v2'&&<span>with probabilities</span>}</h4>
      <div className="table-scroll roi-table"><table><thead><tr><th>ROI</th><th>Grade</th>{model.id==='v2'&&[0,1,2,3,4].map(g=><th key={g}>P({g})</th>)}<th>Box score</th></tr></thead><tbody>{result.detections.map((row,i)=><tr key={i}><td>{i+1}</td><td><span className={`table-grade grade-${row.grade}`}>{row.grade}</span></td>{model.id==='v2'&&[0,1,2,3,4].map(g=><td key={g}>{row.grade_probabilities[String(g)].toFixed(2)}</td>)}<td>{score(row.detector_confidence)}</td></tr>)}</tbody></table></div>
      {model.id==='v1'?<p className="muted">Crop probabilities: <span>Not provided</span>.</p>:<p className="muted">All per-crop grade probabilities shown above are uncalibrated. Ordinal grades need not equal the largest P(g).</p>}
      <p className="muted">Image grade = maximum crop grade. Box scores measure detection, not MGI confidence. No image-level probability distribution is provided.</p>
      <p className="attention-warning">Tooth/perigingival ROI predictions, not ground-truth TXT annotations or clinical gingival boundaries.</p>
      <details><summary>ROI interpretation</summary><p className="muted">Indices are display order, not tooth numbers. Classification includes 15% context padding. Whole-image MGI 0 has no evaluation support. Grad-CAM is not provided by this ROI endpoint.</p></details>
    </>}
    <ModelDetails result={result}/>
  </div>;
}
function Feedback({id,value,onChange,reviewed,disabled}){
  const update=(key,v)=>onChange({...value,[key]:v});
  return <fieldset className="review-fields" disabled={disabled}><legend>{reviewed?'Doctor feedback':'Developer observations'}</legend>
    <div className="agreement-options" role="group" aria-label={`${id} agreement`}>{['Agree','Disagree','Uncertain'].map(label=><button key={label} type="button" className={`agreement-${label.toLowerCase()}`} aria-pressed={value.agreement===label} onClick={()=>update('agreement',value.agreement===label?'':label)}>{label}</button>)}</div>
    <div className="feedback-selects"><label>Reviewer-proposed MGI<select aria-label={`${id} clinician grade`} value={value.grade??''} onChange={e=>update('grade',e.target.value)}><option value="">Not provided</option>{[0,1,2,3,4].map(g=><option key={g}>{g}</option>)}</select></label>
    <label>Reason<select aria-label={`${id} reason`} value={value.reason||''} onChange={e=>update('reason',e.target.value)}><option value="">Not provided</option>{['Grade mismatch','Questionable attention','ROI coverage','Image quality','Other'].map(x=><option key={x}>{x}</option>)}</select></label></div>
    <label>Notes · no patient identifiers<textarea aria-label={`${id} notes`} maxLength={1000} placeholder="Optional comments about this model output" value={value.notes||''} onChange={e=>update('notes',e.target.value)}/></label>
  </fieldset>;
}

// Export an explicit allowlist only: no image, filename, input hash or profile.
export function feedbackDocument(mode,assessment,runs,feedback){
  return {schema:'pp1-vision-feedback-v1',review_mode:mode,clinically_reviewed:mode==='doctor',
    independent_assessment:mode==='doctor'?assessment:null,automatic_retraining:false,
    models:MODELS.map(m=>{const run=runs[m.id];const r=run.result||{};return {
      model:m.name,status:run.status,predicted_mgi_grade:r.predicted_grade??r.image_mgi_grade??null,
      fold:r.fold??null,checkpoint_sha256:r.checkpoint_sha256??null,
      detector_checkpoint_sha256:r.detector_checkpoint_sha256??null,classifier_checkpoint_sha256:r.classifier_checkpoint_sha256??null,
      reviewer_role:mode==='doctor'?'clinician':'developer',agreement:feedback[m.id]?.agreement||null,
      reviewer_grade:feedback[m.id]?.grade===''||feedback[m.id]?.grade==null?null:Number(feedback[m.id].grade),
      reason:feedback[m.id]?.reason||null,notes:feedback[m.id]?.notes||''};})};
}
function csvDocument(document){
  const columns=['review_mode','clinically_reviewed','independent_assessment','model','status','predicted_mgi_grade','fold','checkpoint_sha256','detector_checkpoint_sha256','classifier_checkpoint_sha256','reviewer_role','agreement','reviewer_grade','reason','notes'];
  // Quote fields and neutralise spreadsheet formulas in free text.
  const cell=value=>{let s=String(value??'');if(/^[\s]*[=+\-@]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
  return [columns.join(','),...document.models.map(row=>columns.map(key=>cell(({review_mode:document.review_mode,clinically_reviewed:document.clinically_reviewed,independent_assessment:document.independent_assessment,...row})[key])).join(','))].join('\r\n');
}
export default function DoctorVision(){
  const [mode,setMode]=useState('doctor'),[file,setFile]=useState(null),[preview,setPreview]=useState(''),[consent,setConsent]=useState(false);
  const [assessment,setAssessment]=useState(''),[recorded,setRecorded]=useState(null),[runs,setRuns]=useState(emptyRuns),[feedback,setFeedback]=useState({});
  const [runtimes,setRuntimes]=useState({}),[running,setRunning]=useState(false),[error,setError]=useState(''),[format,setFormat]=useState('json');
  const generation=useRef(0),controller=useRef(null),inFlight=useRef(false),input=useRef(null);
  useEffect(()=>{let live=true;MODELS.forEach(async model=>{try{const response=await fetch(model.status);if(!response.ok)throw Error();const status=await response.json();if(live)setRuntimes(old=>({...old,[model.id]:status}));}catch{if(live)setRuntimes(old=>({...old,[model.id]:{ready:false,message:'Runtime status unavailable.'}}));}});return()=>{live=false;generation.current++;controller.current?.abort();};},[]);
  useEffect(()=>{if(!file){setPreview('');return;}const url=URL.createObjectURL(file);setPreview(url);return()=>URL.revokeObjectURL(url);},[file]);
  function clearCase(){generation.current++;controller.current?.abort();inFlight.current=false;setRunning(false);setRuns(emptyRuns());setFeedback({});setAssessment('');setRecorded(null);setError('');}
  function chooseFile(selected){
    clearCase();setConsent(false);setFile(null);
    if(!selected)return;
    if(!['image/jpeg','image/png'].includes(selected.type)||selected.size===0||selected.size>8*1024*1024){setError('Choose a nonempty JPG or PNG, at most 8 MiB.');if(input.current)input.current.value='';return;}
    setFile(selected);
  }
  function choosePhoto(e){chooseFile(e.target.files?.[0]);}
  function reset(){clearCase();setFile(null);setConsent(false);if(input.current)input.current.value='';}
  async function runAll(){
    if(inFlight.current||!file||!consent||(mode==='doctor'&&recorded===null))return;
    const selected=file,caseGeneration=++generation.current;const abort=new AbortController();controller.current=abort;inFlight.current=true;
    setRunning(true);setError('');setFeedback({});setRuns(Object.fromEntries(MODELS.map(m=>[m.id,{status:'Queued'}])));
    const active=()=>generation.current===caseGeneration;
    const update=(id,value)=>{if(active())setRuns(old=>({...old,[id]:value}));};
    try{
      const bytes=await selected.arrayBuffer();const digest=await crypto.subtle.digest('SHA-256',bytes);
      const expected=Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,'0')).join('');
      for(const model of MODELS){
        if(!active())break;
        if(!runtimes[model.id]?.ready){update(model.id,{status:'Unavailable',error:runtimes[model.id]?.message||'Runtime is not ready.'});continue;}
        update(model.id,{status:'Running'});
        try{
          const response=await fetch(model.endpoint,{method:'POST',headers:{'Content-Type':selected.type,'X-Component2-Demo':'1','X-Component2-Photo-Consent':'local-demo'},body:selected,signal:abort.signal});
          const result=await response.json();if(!response.ok)throw Error(result.error||'Inference failed.');
          if(result.input_sha256!==expected)throw Error('Input identity could not be verified. Start the updated local API.');
          update(model.id,{status:'Success',result});
        }catch(e){if(!active())break;update(model.id,{status:'Failed',error:e.message});}
      }
    }catch(e){if(active()){setError(e.message);setRuns(old=>Object.fromEntries(Object.entries(old).map(([key,value])=>[key,value.status==='Queued'?{status:'Failed',error:'Photo preparation failed.'}:value])));}}
    finally{if(active()){inFlight.current=false;setRunning(false);}}
  }
  function exportFeedback(){
    const document=feedbackDocument(mode,recorded,runs,feedback);const contents=format==='json'?JSON.stringify(document,null,2):csvDocument(document);
    const blob=new Blob([contents],{type:format==='json'?'application/json':'text/csv;charset=utf-8'});const url=URL.createObjectURL(blob);
    const a=window.document.createElement('a');a.href=url;a.download=`pp1-vision-feedback.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  const hasResults=MODELS.some(m=>runs[m.id].status==='Success');
  return <section className="doctor-demo" data-testid="doctor-demo">
    <div className="vision-toolbar"><span>VISION ANALYSIS <small>One photo · four model workflows</small></span><div className="mode-switch" role="group" aria-label="Review mode">{[['doctor','Doctor Review Mode'],['developer','Developer Demo Mode']].map(([value,label])=><button key={value} className={mode===value?'':'secondary'} aria-pressed={mode===value} onClick={()=>{if(mode!==value){clearCase();setMode(value);}}}>{label}</button>)}</div></div>
    <section className="step-panel upload-panel"><h2><span className="step-number">1</span>Upload intraoral photo</h2>
      <div className="upload-layout"><div className="upload-drop" onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();chooseFile(e.dataTransfer.files?.[0]);}}>
        <input ref={input} className="sr-only" aria-label="Intraoral photo" type="file" accept="image/jpeg,image/png" onChange={choosePhoto}/>
        <button className="drop-button" type="button" onClick={()=>input.current?.click()}><Icon name="image" size={30}/><strong>Drag & drop an image here</strong><span>or click to choose</span><small>JPG / PNG · max 8 MiB</small></button>
      </div><figure className="source-preview">{preview?<><img src={preview} alt="Uploaded original intraoral photo"/><button type="button" className="remove-photo" aria-label="Remove uploaded photo" onClick={reset}><Icon name="close" size={16}/></button></>:<div className="preview-placeholder"><Icon name="tooth" size={40}/><span>Your photo preview</span></div>}<figcaption>Original upload · browser preview</figcaption></figure>
      <div className="upload-actions"><label className="check-label"><input aria-label="Photo permission" type="checkbox" checked={consent} onChange={e=>{if(!e.target.checked)clearCase();setConsent(e.target.checked);}}/>I have permission to use this image for research and demonstration purposes.</label>
        <button className="run-all" onClick={runAll} disabled={!file||!consent||running||MODELS.some(m=>runtimes[m.id]===undefined)||(mode==='doctor'&&recorded===null)}><Icon name="play" size={17}/>Run All Four Models</button>
        <p className="muted" role="status">{running?'Running sequentially on this Mac. Each card reports its own status.':'The same image runs through the main candidate, baseline and two ROI comparisons.'}</p>
        <button className="text-button" onClick={reset}>Reset case</button>
      </div></div>
      {mode==='doctor'?<div className="assessment-row"><div><strong>Doctor’s independent assessment</strong><p>Record before revealing predictions. Select “Cannot assess” if the photo is insufficient.</p></div><label className="sr-only" htmlFor="independent-grade">Independent MGI assessment</label><select id="independent-grade" aria-label="Independent MGI assessment" disabled={!file||recorded!==null} value={assessment} onChange={e=>setAssessment(e.target.value)}>{gradeOptions}</select><button className="secondary" disabled={!file||!assessment||recorded!==null} onClick={()=>setRecorded(assessment)}>Record independent assessment</button>{recorded!==null&&<span className="recorded-assessment" role="status"><Icon name="check" size={16}/>{/^\d$/.test(recorded)?`MGI ${recorded}`:recorded} recorded</span>}</div>:<p className="developer-notice" role="status">Developer testing · not clinically reviewed. Observations do not become clinician assessments.</p>}
    </section>
    <p className="research-note">Experimental, provisional outputs. No diagnosis or validated disease localisation. Whole-image MGI 0 is unsupported in evaluation. Photos stay local; no automatic permanent storage.</p>
    {error&&<p className="error" role="alert">{error}</p>}
    <section className="step-panel predictions-panel" id="model-results"><h2><span className="step-number">2</span>AI model predictions <small>Same photo · four model workflows</small></h2>
    <div className="model-grid">{MODELS.map(model=>{const run=runs[model.id];return <article className={`model-card model-${model.id}`} key={model.id} data-testid={`model-${model.id}`}><header className="model-header"><span className="model-letter">{model.letter}</span><div><h3>Model {model.letter} · {model.name}</h3><p>{model.detail}</p></div><span className={`model-status status-${run.status.toLowerCase()}`} role="status">{run.status}</span></header>
      {run.status==='Not run'&&<div className="model-placeholder"><Icon name={model.whole?'image':'tooth'} size={38}/><strong>{runtimes[model.id]===undefined?'Checking local runtime…':runtimes[model.id]?.ready?'Ready to analyse your photo':runtimes[model.id]?.message||'Runtime unavailable.'}</strong><p>Upload one photo and run the comparison to see this model’s result.</p></div>}
      {['Queued','Running'].includes(run.status)&&<div className="model-placeholder"><span className="loading-ring"/><strong>{run.status==='Queued'?'Waiting for its turn':'Analysing on this Mac…'}</strong></div>}
      {run.error&&<p className="error" role="alert">{run.error}</p>}
      {run.result&&<ModelOutput model={model} result={run.result}/>}
    </article>;})}</div></section>
    <section className="step-panel feedback-panel" id="doctor-feedback"><h2><span className="step-number">3</span>{mode==='doctor'?'Doctor evaluation & feedback':'Developer evaluation & observations'}</h2>
      <div className="review-grid"><aside className="assessment-summary"><Icon name="tooth" size={28}/><h3>{mode==='doctor'?'Independent assessment':'Developer Demo Mode'}</h3><strong>{mode==='doctor'?(recorded===null?'Not recorded':/^\d$/.test(recorded)?`MGI ${recorded}`:recorded):'Not clinically reviewed'}</strong><p>{mode==='doctor'?'Assessment is recorded above before AI predictions are revealed.':'No clinician assessment has been recorded in this mode.'}</p><small>Feedback stays separate from model predictions. No automatic retraining.</small></aside>
      {MODELS.map(model=><section className={`feedback-card feedback-${model.id}`} key={model.id} data-model={model.id}><h3>Model {model.letter} feedback</h3><Feedback id={model.id} value={feedback[model.id]||{}} onChange={value=>setFeedback(old=>({...old,[model.id]:value}))} reviewed={mode==='doctor'} disabled={!runs[model.id].result}/></section>)}</div>
      <div className="export-panel"><p>Session-only feedback. Reset/reload clears it. Export excludes image bytes, filename, input-photo hash and patient-ID fields; do not enter identifiers in notes.</p><label>Download format<select aria-label="Feedback export format" value={format} onChange={e=>setFormat(e.target.value)}><option value="json">JSON</option><option value="csv">CSV</option></select></label><button onClick={exportFeedback} disabled={!hasResults||running}><Icon name="feedback" size={17}/>Export Feedback</button></div>
    </section>
    <details className="processing-note"><summary>Photo handling & research limitations</summary><p>Embedded ICC is converted to sRGB; missing ICC is assumed sRGB. Browser preview and colour-managed model views can differ. EfficientNet is the proposal main candidate and ResNet the baseline. Labels are provisional and participant independence/clinical validity remain unverified. Original trained attention is preserved, including attention on lips or other peripheral regions. ROI boxes are predictions, not source annotations.</p></details>
  </section>;
}
