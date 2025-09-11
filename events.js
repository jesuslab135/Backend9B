(function(){
function refreshButtons(){
document.querySelectorAll('[data-action]').forEach(btn=>{
const act = btn.getAttribute('data-action');
const current = Sim.getState();
btn.disabled = (act===current) || Sim.FORBIDDEN(current, act);
});
}


// Wire botones de acción
document.querySelectorAll('[data-action]').forEach(btn=>{
btn.addEventListener('click', ()=>{
const ok = Sim.setState(btn.getAttribute('data-action'));
if(ok) refreshButtons();
});
});


// Perfil (intervalo de muestreo)
const perfilSel = document.getElementById('perfil');
perfilSel.addEventListener('change', ()=>{ Sim.setProfile(perfilSel.value); });


// Primera actualización de botones al cargar
window.addEventListener('load', refreshButtons);
})();