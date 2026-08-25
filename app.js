const tg=window.Telegram?.WebApp;
if(tg){tg.ready();tg.expand();tg.setHeaderColor("#07090e");tg.setBackgroundColor("#07090e");}
const API_URL=""; // If backend is on another domain, put its HTTPS URL here.
const initData=tg?.initData||"";
let S = JSON.parse(localStorage.getItem("duty_save")) || {
  balance: 0,
  energy: 5000,
  max_energy: 5000,
  level: 1,
  tap_power: 1,
  referral_count: 0,
  wallet: null
};
const $=x=>document.getElementById(x);
function render(){ $("balance").textContent=S.balance.toLocaleString();$("energy").textContent=S.energy.toLocaleString();$("max").textContent=S.max_energy.toLocaleString();$("level").textContent=S.level;$("power").textContent=S.tap_power;$("energybar").style.width=Math.max(0,Math.min(100,S.energy/S.max_energy*100))+"%";localStorage.setItem("duty_save", JSON.stringify(S));}
function toast(t){$("toast").textContent=t;$("toast").classList.add("show");setTimeout(()=>$("toast").classList.remove("show"),1800)}
async function load(){if(!initData){toast("Open inside Telegram");return;}try{const r=await fetch(API_URL+"/api/user",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({init_data:initData})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Server error");S={...S,...d};render();}catch(e){toast(e.message)}}
async function tap(){if(S.energy<=0){toast("No energy");return;}S.balance+=S.tap_power;S.energy=Math.max(0,S.energy-1);render();try{const r=await fetch(API_URL+"/api/tap",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({init_data:initData})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Server error");S={...S,...d};render();}catch(e){toast(e.message)}}
async function boost(){try{const r=await fetch(API_URL+"/api/boost",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({init_data:initData})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Boost failed");S.balance=d.balance;S.tap_power=d.tap_power;render();toast("⚡ Tap Power upgraded!");}catch(e){toast(e.message)}}
async function daily(){try{const r=await fetch(API_URL+"/api/daily",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({init_data:initData})});const d=await r.json();if(!r.ok)throw new Error(d.detail||"Server error");S={...S,...d};render();toast("🎁 Daily reward claimed!");}catch(e){toast(e.message)}}
function regen(){const now=Date.now();if(!S.energy_updated_at)S.energy_updated_at=now;const gained=Math.floor((now-S.energy_updated_at)/3000);if(gained>0){S.energy=Math.min(S.max_energy,S.energy+gained);S.energy_updated_at+=gained*3000;render();}}
setInterval(regen,1000);
$("tap")?.addEventListener("click",tap);
$("boost")?.addEventListener("click",boost);
$("daily")?.addEventListener("click",daily);
load();
render();
