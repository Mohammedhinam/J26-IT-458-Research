import React, {useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import DoctorVision from './DoctorVision';
import Icon from './Icons';

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
    <section className="card" data-testid="photo-model-comparison">
      <h2>Same 680-image OOF comparison</h2>
      <p className="notice">These aggregate results compare model workflows on the same development folds. A single uploaded photo cannot show which model is more accurate.</p>
      <div className="table-scroll" role="region" aria-label="680-image model comparison" tabIndex="0"><table><thead><tr><th>Workflow</th><th>Accuracy</th><th>Macro-F1</th><th>Grade 1 recall</th><th>Grade 2 recall</th><th>Runs on new photo?</th></tr></thead>
        <tbody>{evidence.photo_model_comparison_680.rows.map(row=><tr key={row.name}><th scope="row">{row.name}</th><td>{(100*row.accuracy).toFixed(2)}%</td><td>{row.macro_f1.toFixed(3)}</td>
          <td>{row.correct_per_grade[0]}/{row.support[0]}</td><td>{row.correct_per_grade[1]}/{row.support[1]}</td><td>{row.new_photo_inference}</td></tr>)}</tbody></table></div>
      <p className="muted">The ROI rows can run with fold 00 for illustration; neither is a final all-development refit. The EfficientNet 52.21% row has saved OOF results but no packaged fitted Logistic checkpoint for new-photo inference. All labels remain provisional.</p>
    </section>
  </>;
}
function App(){
  const [schema,setSchema]=useState(null),[profile,setProfile]=useState({}),[tab,setTab]=useState('vision');
  const [result,setResult]=useState(null),[original,setOriginal]=useState(null),[scenario,setScenario]=useState(null);
  const [smoking,setSmoking]=useState(''),[days,setDays]=useState('7'),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [vision,setVision]=useState(null),[visionEvidence,setVisionEvidence]=useState(null);
  const [questionnaireEvidence,setQuestionnaireEvidence]=useState(null);
  const [section,setSection]=useState('');
  useEffect(()=>{if(tab==='vision'){api('/api/vision').then(setVision).catch(()=>setVision(null));api('/api/vision/evidence').then(setVisionEvidence).catch(()=>setVisionEvidence(null));}},[tab]);
  useEffect(()=>{if(!section)return;const frame=requestAnimationFrame(()=>{const target=document.getElementById(section);if(target?.tagName==='DETAILS')target.open=true;target?.scrollIntoView({behavior:'auto',block:'start'});});return()=>cancelAnimationFrame(frame);},[tab,section]);
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
  function navigate(next,anchor=''){
    setTab(next);setSection(anchor);setError('');
    if(!anchor){window.scrollTo({top:0});return;}
    // Existing sections can scroll immediately, including a repeated sidebar click.
    if(tab===next){const target=document.getElementById(anchor);if(target?.tagName==='DETAILS')target.open=true;target?.scrollIntoView({behavior:'auto',block:'start'});}
  }
  const active=section||tab;
  return <div className="demo-shell"><header className="topbar">
    <div className="brand"><span className="brand-mark"><Icon name="tooth" size={34}/></span><div><h1>PP1 Demo</h1><p>Gingival Image Assessment · MGI</p></div></div>
    <div className="research-label"><Icon name="flask" size={26}/><span><strong>Research Use Only</strong><small>Not for clinical diagnosis</small></span></div>
  </header><aside className="sidebar"><nav aria-label="Main navigation">
    <button aria-label="Vision · exploratory evidence" aria-current={active==='vision'?'page':undefined} disabled={busy} onClick={()=>navigate('vision')}><Icon name="image"/><span><strong>Vision AI</strong><small>Image analysis</small></span></button>
    <button aria-label="Questionnaire · live explanation" aria-current={active==='questionnaire'?'page':undefined} disabled={busy} onClick={()=>navigate('questionnaire')}><Icon name="questionnaire"/><span><strong>Questionnaire</strong><small>Previous-treatment model</small></span></button>
    <button aria-label="Results & Feedback" aria-current={active==='doctor-feedback'?'page':undefined} disabled={busy} onClick={()=>navigate('vision','doctor-feedback')}><Icon name="feedback"/><span><strong>Results & Feedback</strong><small>Doctor review</small></span></button>
    <button aria-label="Model Comparison" aria-current={active==='model-comparison'?'page':undefined} disabled={busy} onClick={()=>navigate('vision','model-comparison')}><Icon name="chart"/><span><strong>Model Comparison</strong><small>Research metrics</small></span></button>
    <button aria-label="About the project" aria-current={active==='about-project'?'page':undefined} disabled={busy} onClick={()=>navigate(tab,'about-project')}><Icon name="about"/><span><strong>About</strong><small>Project information</small></span></button>
  </nav><div className="sidebar-footer"><span className="local-dot"/> Local execution<small>RP-J26-IT-458 · Component 2<br/>Two independent research branches</small></div></aside>
  <div className="workspace"><div className="workspace-status" role="status" aria-live="polite">{busy?'Checking inputs and explanation…':schema?'Ready · local execution':'Loading local model interface…'}</div>
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
    {tab==='vision'&&<main><DoctorVision/>
      <details className="card research-evidence" id="model-comparison"><summary>Existing research evidence & saved examples · separate from this upload</summary>
      <VisionEvidence evidence={visionEvidence}/>
      {vision?.examples.map(sample=><section className="card" key={sample.id}><h2>{sample.id} · predicted MGI {sample.predicted_grade}</h2><p className="muted">Saved output · provisional reference {sample.provisional_label}. {sample.probabilities.map((p,i)=>`MGI ${i+1}: ${(p*100).toFixed(1)}%`).join(' | ')}</p><Views views={sample.views} prefix="/vision/" id={sample.id}/></section>)}
      {vision&&<p className="muted">{vision.attribution} {vision.transformation_notice}</p>}</details></main>}
    <details className="card about-panel" id="about-project"><summary>About this research demonstration</summary><p>Dual-Branch Explainable AI & Interactive Risk Simulator for Periodontal Disease Screening · Component 2 · RP-J26-IT-458.</p><p>Vision estimates visible gingival inflammation from a photo. The independent questionnaire estimates self-reported previous gum treatment. Their outputs are never combined. This local research demo does not provide a diagnosis.</p></details>
    <footer>Branches remain separate. Vision labels, participant independence and final evaluation remain pending. Neither branch is clinically validated. No automatic persistence. Feedback downloads only when explicitly requested.</footer></div></div>;
}
createRoot(document.getElementById('root')).render(<App/>);
