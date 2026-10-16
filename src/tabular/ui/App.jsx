import React, {useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';

// All requests stay on the local API; no questionnaire or image is stored here.
async function api(path,data){
  const options=data===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json','X-Component2-Demo':'1'},body:JSON.stringify(data)};
  const response=await fetch(path,options);const result=await response.json();
  if(!response.ok)throw new Error(result.error||'Request failed');return result;
}
function Prediction({result}){
  if(!result)return <p>Choose “Explain this profile” to begin.</p>;
  const rows=[...result.contributions].sort((a,b)=>Math.abs(b.contribution_log_odds)-Math.abs(a.contribution_log_odds));
  const scale=Math.max(...rows.map(r=>Math.abs(r.contribution_log_odds)),.001);
  const sum=rows.reduce((n,r)=>n+r.contribution_log_odds,0);
  return <><p className="muted">Model probability of previous treatment</p><div className="big" data-testid="probability">{(result.probability*100).toFixed(2)}%</div>
    <p className="muted">Raw development reference; not separately calibrated.</p><h3>Why this output?</h3>
    <p className="muted">SHAP in log-odds: red raises and blue lowers this output relative to the base value. Associations, not causal effects.</p>
    {rows.map(r=><div className="shaprow" key={r.field}><span>{r.label}</span><div className="track"><div className={'bar'+(r.contribution_log_odds<0?' negative':'')} style={{width:(100*Math.abs(r.contribution_log_odds)/scale)+'%'}}/></div><span>{r.contribution_log_odds.toFixed(3)}</span></div>)}
    <p className="muted">Base {result.base_log_odds.toFixed(4)} + contributions {sum.toFixed(4)} = {result.raw_log_odds.toFixed(4)} log-odds. Additivity check passed.</p>
    <p className="muted">Smoking/cleaning pair: {result.support.smoking_cleaning_pair_count} development examples. Full-profile reliability is unverified.</p>
    <ul>{result.support.warnings.map(w=><li key={w}>{w}</li>)}</ul></>;
}
function Views({views,prefix='',id='photo'}){
  return <div className="views">{['original','heatmap','overlay'].map(name=><figure key={name}><img src={prefix+views[name]} alt={id+' '+name}/><figcaption>{name==='original'?'Colour-managed display preview':name==='heatmap'?'Grad-CAM · model attention':'Aligned overlay'}</figcaption></figure>)}</div>;
}
function QuestionnaireEvidence({evidence}){
  if(!evidence)return <section className="card"><p>Matching final questionnaire evidence is unavailable. No evaluation runs from this page.</p></section>;
  return <section className="card" data-testid="questionnaire-final-evidence"><h2>Completed frozen questionnaire evaluation</h2>
    <p>{evidence.n.toLocaleString('en-US')} held-out participants: {evidence.yes} reported Yes / {evidence.no.toLocaleString('en-US')} No. Existing results only; no evaluation rerun.</p>
    <div className="table-scroll" role="region" aria-label="Questionnaire final results" tabIndex="0"><table><thead><tr><th>Model</th><th>AUROC</th><th>Brier</th><th>Cutoff</th><th>Sensitivity</th><th>Specificity</th></tr></thead>
      <tbody>{evidence.models.map(row=><tr key={row.name}><th scope="row">{row.name}</th><td>{row.AUROC.toFixed(4)}</td><td>{row.Brier.toFixed(4)}</td><td>{row.cutoff.toFixed(2)}</td><td>{(100*row['Sensitivity frozen']).toFixed(2)}%</td><td>{(100*row['Specificity frozen']).toFixed(2)}%</td></tr>)}</tbody></table></div>
    <ul>{evidence.limitations.map(text=><li key={text}>{text}</li>)}</ul></section>;
}
function VisionEvidence({evidence}){
  if(!evidence)return <p>Verified aggregate evidence is loading.</p>;
  const old=evidence.historical_validation53;
  return <>
    <section className="card" data-testid="historical53"><h2>Historical pilot · 53 Validation images</h2>
      <p>ResNet last-bottleneck v3. Accuracy {(old.accuracy*100).toFixed(2)}%; macro-F1 {old.macro_f1.toFixed(3)}.</p>
      <p>Grade-2 recall: {old.correct_per_grade[1]}/{old.support[1]}. Repeated development/checkpoint selection; not final evaluation.</p>
      <p>Grad-CAM examples below come from this historical pilot.</p></section>
    <section className="card" data-testid="training680"><h2>Frozen-feature comparison · 680 Training OOF images</h2>
      <p className="notice">{evidence.comparability}</p>
      <p>Same 680 source records, provisional labels and five content-group folds for these rows. Scaler and classifier fitted inside each training fold.</p>
      <p className="muted">On a narrow screen, scroll the table sideways to see Macro-F1 and each grade’s recall.</p>
      <div className="table-scroll" role="region" aria-label="Training680 comparison table" tabIndex="0"><table><thead><tr><th>Configuration</th><th>Accuracy</th><th>Macro-F1</th><th>Balanced accuracy</th><th>Grade 1 recall</th><th>Grade 2 recall</th><th>Grade 3 recall</th><th>Grade 4 recall</th></tr></thead>
        <tbody>{evidence.training680_oof.map(row=><tr key={row.name}><th scope="row">{row.name}</th><td>{(row.accuracy*100).toFixed(2)}%</td><td>{row.macro_f1.toFixed(3)}</td><td>{row.balanced_accuracy.toFixed(3)}</td>{row.recall.map((r,i)=><td key={i}>{row.correct_per_grade[i]}/{row.support[i]} ({(r*100).toFixed(1)}%)</td>)}</tr>)}</tbody></table></div>
      <ul>{evidence.limitations.map(text=><li key={text}>{text}</li>)}</ul></section>
  </>;
}
function App(){
  const [schema,setSchema]=useState(null),[profile,setProfile]=useState({}),[tab,setTab]=useState('questionnaire');
  const [result,setResult]=useState(null),[original,setOriginal]=useState(null),[scenario,setScenario]=useState(null);
  const [smoking,setSmoking]=useState(''),[days,setDays]=useState('7'),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [vision,setVision]=useState(null),[runtime,setRuntime]=useState(null),[photo,setPhoto]=useState(null),[file,setFile]=useState(null);
  const [visionEvidence,setVisionEvidence]=useState(null);
  const [questionnaireEvidence,setQuestionnaireEvidence]=useState(null);
  useEffect(()=>{api('/api/schema').then(s=>{setSchema(s);setProfile(s.example);}).catch(e=>setError(e.message));},[]);
  useEffect(()=>{api('/api/questionnaire/evidence').then(setQuestionnaireEvidence).catch(()=>setQuestionnaireEvidence(null));},[]);
  async function task(work){if(busy)return;setBusy(true);setError('');try{await work();}catch(e){setError(e.message);}finally{setBusy(false);}}
  function clearPrediction(){setOriginal(null);setResult(null);setScenario(null);}
  async function explain(e){e.preventDefault();clearPrediction();await task(async()=>{
    const r=await api('/api/predict',{profile});setResult(r);setOriginal(r.profile);setSmoking(r.profile.SMOKING_STATUS??'');setDays(String(r.profile.OHQ870??0));
  });}
  async function simulate(reset=false){await task(async()=>{
    if(!original)throw new Error('Explain the original profile first');
    const body={original,model_id:schema.model_id};
    if(!reset){if(days==='')throw new Error('Enter cleaning days');body.changes={OHQ870:Number(days)};
      if((smoking||null)!==original.SMOKING_STATUS)body.changes.SMOKING_STATUS=smoking||null;}
    setScenario(null);setResult(null);
    const r=await api(reset?'/api/reset':'/api/what-if',body);setResult(r.scenario);setScenario(r);
    if(reset){setSmoking(original.SMOKING_STATUS??'');setDays(String(original.OHQ870??0));}
  });}
  async function openVision(){setTab('vision');await task(async()=>{const [v,r,e]=await Promise.all([api('/api/vision'),api('/api/vision/runtime'),api('/api/vision/evidence')]);setVision(v);setRuntime(r);setVisionEvidence(e);});}
  async function explainPhoto(e){e.preventDefault();setPhoto(null);await task(async()=>{
    if(!file||file.size>8*1024*1024)throw new Error('Choose a registered JPEG, at most 8 MiB');
    const response=await fetch('/api/vision/photo',{method:'POST',headers:{'Content-Type':'image/jpeg','X-Component2-Demo':'1'},body:file});
    const r=await response.json();if(!response.ok)throw new Error(r.error||'Photo explanation failed');setPhoto(r);
  });}
  return <><header><div className="eyebrow">RP-J26-IT-458 · COMPONENT 2 · LOCAL PP1 DEMO</div><h1>Understand the model’s response</h1><p className="intro">Two independent research branches. Explore a fictional questionnaire profile and inspect exploratory Vision explanations.</p></header>
    <nav><button disabled={busy} aria-selected={tab==='questionnaire'} onClick={()=>{setTab('questionnaire');setError('');}}>Questionnaire · live explanation</button><button disabled={busy} className="secondary" aria-selected={tab==='vision'} onClick={openVision}>Vision · exploratory evidence</button></nav>
    <p role="status" aria-live="polite">{busy?'Checking inputs and explanation…':schema?'Ready · local execution':'Loading local model interface…'}</p>
    {error&&<div className="error" role="alert">{error}</div>}
    {tab==='questionnaire'&&schema&&<main><p className="notice">Predicts reported <strong>previous gum treatment</strong>. Not current disease, future risk or a clinical recommendation. Use fictional profiles; income and education follow US NHANES definitions.</p>
      <QuestionnaireEvidence evidence={questionnaireEvidence}/>
      <div className="grid"><section className="card"><h2>1. Fictional example profile</h2><p className="muted">12 model inputs. Smoking combines two source questions. Unknown answers stay explicit.</p>
      <form onSubmit={explain}><fieldset disabled={busy}><div className="formgrid">{schema.fields.map(f=><label key={f.key} htmlFor={'field_'+f.key}>{f.label}{f.options?
        <select id={'field_'+f.key} value={profile[f.key]??''} onChange={e=>{setProfile({...profile,[f.key]:e.target.value||null});clearPrediction();}}><option value="">Unknown / not answered</option>{f.options.map(([code,text])=><option key={code} value={code}>{text}</option>)}</select>:
        <input id={'field_'+f.key} type="number" min={f.key==='RIDAGEYR'?30:0} max={f.key==='RIDAGEYR'?80:f.key==='OHQ870'?7:5} step={f.key==='INDFMPIR'?'.01':'1'} required={f.key==='RIDAGEYR'} value={profile[f.key]??''} placeholder="Unknown" onChange={e=>{setProfile({...profile,[f.key]:e.target.value===''?null:Number(e.target.value)});clearPrediction();}}/>}</label>)}</div>
        <div className="actions"><button type="submit">Explain this profile</button><button type="button" className="secondary" onClick={()=>{setProfile(schema.example);clearPrediction();setError('');}}>Restore example profile</button></div></fieldset></form></section>
      <div><section className="card"><h2>2. Prediction & contribution check</h2><Prediction result={result}/></section>
      <section className="card"><h2>3. What-if · model sensitivity</h2><p className="muted">Age/history stay fixed. Changing answers does not change past treatment or prove a health benefit.</p>
        <fieldset disabled={busy||!original}><div className="formgrid"><label>Scenario smoking status<select aria-label="Scenario smoking status" value={smoking} onChange={e=>setSmoking(e.target.value)}><option value="">Unknown / unchanged</option>{schema.fields.find(f=>f.key==='SMOKING_STATUS').options.map(([code,text])=><option key={code} value={code}>{text}</option>)}</select></label>
        <label>Scenario cleaning days<input aria-label="Scenario cleaning days" type="number" min="0" max="7" step="1" value={days} onChange={e=>setDays(e.target.value)}/></label></div>
        <div className="actions"><button onClick={()=>simulate()}>Compare scenario</button><button className="secondary" onClick={()=>simulate(true)}>Reset scenario</button></div></fieldset>
        {scenario&&<div data-testid="scenario"><p>{scenario.is_reset?'Reset: original prediction restored exactly.':`Original ${(scenario.original.probability*100).toFixed(2)}% → Scenario ${(scenario.scenario.probability*100).toFixed(2)}%`}</p><p className="notice">{scenario.notice}</p></div>}
      </section></div></div></main>}
    {tab==='vision'&&<main><p className="notice">Provisional labels; non-clinical; non-final; participant independence unverified. Exploratory outputs cover MGI 1–4. Whole-image MGI 0 is unsupported; research definitions remain 0–4.</p>
      <VisionEvidence evidence={visionEvidence}/><p>Grad-CAM shows model attention, not clinical boundaries. The 181 holds and final Test remain excluded.</p>
      <section className="card"><h2>New-photo explanation</h2><p>{runtime?.ready?(runtime.synthetic_only?'Generated-image verification runtime only.':'Exploratory runtime for registered inputs only.'):(runtime?.message||'Checking runtime…')}</p><p className="muted">Only separately registered RGB JPEGs with a qualified colour profile. Unsupported photographs are rejected; no clinical diagnosis.</p>
      <form onSubmit={explainPhoto}><fieldset disabled={busy||!runtime?.ready}><label>Registered JPEG photo<input type="file" accept="image/jpeg" onChange={e=>{setFile(e.target.files[0]);setPhoto(null);}}/></label><div className="actions"><button>Predict and explain photo</button></div></fieldset></form>
      {photo&&<><h3>{photo.synthetic_only?'Synthetic check':'Exploratory prediction'} · MGI {photo.predicted_grade}</h3><p>{photo.probabilities.map((p,i)=>`MGI ${photo.mgi_grades[i]}: ${(p*100).toFixed(1)}%`).join(' | ')}</p><p>{photo.meaning} · {photo.explanation_status}</p><Views views={photo.views_png_base64} prefix="data:image/png;base64,"/><p className="muted">{photo.display_evidence.colour_policy}</p></>}
      </section>{vision?.examples.map(sample=><section className="card" key={sample.id}><h2>{sample.id} · predicted MGI {sample.predicted_grade}</h2><p className="muted">Saved output · provisional reference {sample.provisional_label}. {sample.probabilities.map((p,i)=>`MGI ${i+1}: ${(p*100).toFixed(1)}%`).join(' | ')}</p><Views views={sample.views} prefix="/vision/" id={sample.id}/></section>)}
      {vision&&<p className="muted">{vision.attribution} {vision.transformation_notice}</p>}</main>}
    <footer>Branches remain separate. Vision labels, participant independence and final evaluation remain pending. Neither branch is clinically validated. No information is saved by this interface.</footer></>;
}
createRoot(document.getElementById('root')).render(<App/>);
