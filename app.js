const NAMES = ['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'];
const MAJOR = [0,2,4,5,7,9,11];
const MINOR = [0,2,3,5,7,8,10];
const INSTRUMENTS = {'Grand piano':0,'Electric piano':4,'Guitar':24,'Strings':48,'Flute':73,'Synth lead':80};
const LEVELS = ['Starter','In key','Chromatic'];
const STORAGE_KEY = 'pitchlab.progress.v2';
const $ = id => document.getElementById(id);
const defaults = {settings:{instrument:'Grand piano',level:'Starter',key:0,scale:'Major',octave:4,reference:true},progress:{correct:0,attempts:0,best_streak:0}};
let saved;
try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY)); } catch { saved = null; }
let settings = {...defaults.settings,...(saved?.settings || {})};
let progress = {...defaults.progress,...(saved?.progress || {})};
let streak = 0;
let round = null;
let lastPitch = null;
let currentAudio = null;

function persist() { localStorage.setItem(STORAGE_KEY,JSON.stringify({settings,progress})); }
function pool() {
  if (settings.level === 'Chromatic') return [...Array(12).keys()];
  const offsets = settings.level === 'Starter' ? [0,2,4] : settings.scale === 'Minor' ? MINOR : MAJOR;
  return offsets.map(offset => (settings.key + offset) % 12);
}
function midi(pitch) { return (Number(settings.octave)+1)*12 + pitch; }
function sound(pitch) {
  if(currentAudio){currentAudio.pause();currentAudio=null;}
  currentAudio = new Audio(`/audio/${INSTRUMENTS[settings.instrument]}/${midi(pitch)}.wav`);
  currentAudio.play().catch(() => {
    $('feedback').className='feedback bad';
    $('feedback').textContent='Sound was blocked. Click Play the note to try again.';
  });
}
function newRound(play=false) {
  let choices=pool().filter(p => p!==lastPitch);
  if (!choices.length) choices=pool();
  const pitch=choices[Math.floor(Math.random()*choices.length)];
  lastPitch=pitch;
  round={pitch,answered:false,guess:null,correct:null};
  render();
  if(play) sound(pitch);
}
function answer(guess) {
  if(round.answered || !pool().includes(guess)) return;
  round.answered=true;round.guess=guess;round.correct=guess===round.pitch;
  progress.attempts++;
  if(round.correct){progress.correct++;streak++;progress.best_streak=Math.max(streak,progress.best_streak);}
  else streak=0;
  persist();render();
}
function reveal(){if(round.answered)return;round.answered=true;round.correct=null;streak=0;render();}
function setOptions(el,pairs){el.replaceChildren(...pairs.map(([v,t])=>{const o=document.createElement('option');o.value=v;o.textContent=t;return o;}));}
function render(){
  setOptions($('level'),LEVELS.map(x=>[x,x]));$('level').value=settings.level;
  setOptions($('key'),NAMES.map((x,i)=>[i,x]));$('key').value=settings.key;
  setOptions($('instrument'),Object.keys(INSTRUMENTS).map(x=>[x,x]));$('instrument').value=settings.instrument;
  $('scale').value=settings.scale;$('octave').value=settings.octave;$('referenceToggle').checked=settings.reference;
  $('scale').disabled=settings.level!=='In key';
  $('levelHint').textContent=settings.level==='Starter'?'Three notes from your chosen tonic. A gentle place to start.':settings.level==='In key'?'All seven notes of the selected major or minor scale.':'All 12 notes, in any key.';
  $('reference').style.display=settings.reference?'':'none';
  $('answers').replaceChildren(...NAMES.map((name,i)=>{
    const b=document.createElement('button');b.className='note';b.textContent=name;b.disabled=!pool().includes(i)||round.answered;
    if(round.answered&&i===round.pitch)b.classList.add('right');
    if(round.answered&&i===round.guess&&round.correct===false)b.classList.add('wrong');
    b.onclick=()=>answer(i);return b;
  }));
  let message='';let className='feedback';
  if(round.answered){
    if(round.correct===true){message='Correct — that was '+NAMES[round.pitch]+'.';className+=' good';}
    else if(round.correct===false){message='That was '+NAMES[round.pitch]+'. You chose '+NAMES[round.guess]+'.';className+=' bad';}
    else message='That was '+NAMES[round.pitch]+'. Give the next one a try.';
  }
  $('feedback').className=className;$('feedback').textContent=message;
  $('accuracy').textContent=progress.attempts?Math.round(100*progress.correct/progress.attempts)+'%':'0%';
  $('streak').textContent=streak;$('best').textContent=progress.best_streak;
  $('reveal').disabled=round.answered;
  drawKeyboard();
}
function drawKeyboard(){
  const white=[0,2,4,5,7,9,11],black=[{n:1,x:10.3},{n:3,x:24.6},{n:6,x:53.2},{n:8,x:67.5},{n:10,x:81.8}];
  const holder=$('keyboard');holder.replaceChildren();
  for(const n of white){const b=document.createElement('button');b.className='white';b.textContent=NAMES[n];b.setAttribute('aria-label','Play '+NAMES[n]);b.onclick=()=>preview(n,b);holder.append(b);}
  for(const {n,x} of black){const b=document.createElement('button');b.className='black';b.textContent=NAMES[n];b.style.left=x+'%';b.setAttribute('aria-label','Play '+NAMES[n]);b.onclick=()=>preview(n,b);holder.append(b);}
}
function preview(note,button){sound(note);button.classList.add('active');setTimeout(()=>button.classList.remove('active'),250);}
for(const id of ['level','key','scale','instrument','octave'])$(id).addEventListener('change',e=>{
  settings[id]=['key','octave'].includes(id)?Number(e.target.value):e.target.value;
  lastPitch=null;persist();newRound(true);
});
$('referenceToggle').addEventListener('change',e=>{settings.reference=e.target.checked;persist();render();});
$('play').onclick=()=>sound(round.pitch);
$('reference').onclick=()=>sound(settings.key);
$('next').onclick=()=>newRound(true);
$('reveal').onclick=reveal;
newRound();
