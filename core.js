(function(){
Sim.updateIndicators = function(hr, steps, spo){
hrVal.textContent = hr + ' bpm'; stepsVal.textContent = steps + ' /min'; spoVal.textContent = spo + ' %';
const dHr = lastDiff(dataBuffer.hr); const dSt = lastDiff(dataBuffer.steps); const dSp = lastDiff(dataBuffer.spo2);
hrTrend.textContent = (dHr>0? '↑':'↓') + Math.abs(dHr).toFixed(0) + ' vs último';
stepsTrend.textContent = (dSt>0? '↑':'↓') + Math.abs(dSt).toFixed(0) + ' vs último';
spoTrend.textContent = (dSp>0? '↑':'↓') + Math.abs(dSp).toFixed(1) + ' vs último';
const r = Sim.STATES[state].ranges;
hrVal.className = 'value ' + (hr<r.hr[0] || hr>r.hr[1] ? 'bad':'');
stepsVal.className = 'value ' + (steps<r.steps[0] || steps>r.steps[1] ? 'bad':'');
spoVal.className = 'value ' + (spo<r.spo2[0] || spo>r.spo2[1] ? 'bad':'');
};


// ======= API de estado/perfil =======
const stateBadge = document.getElementById('stateBadge');


Sim.setState = function(next){
if(Sim.FORBIDDEN(state, next)){
flash(stateBadge, 'Intento inválido: no se puede correr mientras duerme', true);
return false;
}
state = Sim.state = next; configureGenerators();
stateBadge.textContent = `Estado: ${Sim.STATES[state].label}`;
flash(stateBadge, `Cambiado a ${Sim.STATES[state].label}`);
return true;
};


Sim.getState = ()=> state;


Sim.setProfile = function(next){ profile = Sim.profile = next; startAcquisition(); };


function flash(el, msg, warn){
el.textContent = msg;
el.style.borderColor = warn ? '#8a1818' : '#244279';
el.style.background = warn ? '#2a0f12' : '#0b1b33';
setTimeout(()=>{ el.textContent = `Estado: ${Sim.STATES[state].label}`; el.style.borderColor = '#244279'; el.style.background = '#0b1b33'; }, 1600);
}


// ======= Leyenda =======
Sim.buildLegend = function(){
const legend = document.getElementById('legend'); legend.innerHTML='';
Sim.SERIES.forEach(s=>{
const item = document.createElement('label'); item.className='legend-item';
const cb = document.createElement('input'); cb.type='checkbox'; cb.checked = visible[s.key];
cb.addEventListener('change', ()=>{ visible[s.key]=cb.checked; Sim.draw(); });
const dot = document.createElement('span'); dot.className='dot'; dot.style.background = s.color;
const txt = document.createElement('span'); txt.textContent = s.name;
item.append(cb, dot, txt); legend.appendChild(item);
});
};


// ======= Bootstrap =======
Sim.bootstrap = function(){
Sim.buildLegend();
Sim.setState('descanso');
configureGenerators();
for(let i=0;i<12;i++){ pushDataPoint(); }
startAcquisition();
Sim.draw();
};


// init on load
window.addEventListener('load', Sim.bootstrap);
})();