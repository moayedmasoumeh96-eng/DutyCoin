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
async function load(){if(!initData){render();return}try{let r=await fetch(`${API_URL}/api/user`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({init_data:initData})});if(!r.ok)throw 0;S=await r.json();render()}catch(e){toast("Server connection failed")}}
let q=0,timer;
$("tap").onclick=()=>{if(S.energy<=0)return toast("⚡ No energy");S.energy--;S.balance+=S.tap_power;q++;render();clearTimeout(timer);timer=setTimeout(sync,180)}
async function sync(){if(!q||!initData){q=0;return}let n=q;q=0;try{let r=await fetch(`${API_URL}/api/tap`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({init_data:initData,taps:n})});if(!r.ok)throw 0;let d=await r.json();S.balance=d.balance;S.energy=d.energy;render()}catch(e){toast("Tap sync failed");load()}}
setInterval(() => {
  if (S.energy < S.max_energy) {
    S.energy++;
    render();
  }
}, 3000); // 1 energy / 3s, matches the backend regen rate exactly
function open(html){$("content").innerHTML=html;$("sheet").classList.add("open")}
$("close").onclick=()=>$("sheet").classList.remove("open");
$("profile").onclick=()=>open(`<h2>👤 Profile</h2><p>Level ${S.level}<br>Balance: ${S.balance.toLocaleString()} DUTY<br>Energy: ${S.energy}/${S.max_energy}<br>Tap Power: +${S.tap_power}<br>Friends: ${S.referral_count}</p>`);
async function daily(){if(!initData)return toast("Open inside Telegram");try{let r=await fetch(`${API_URL}/api/daily`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({init_data:initData})});let d=await r.json();if(d.ok){S.balance=d.balance;render();toast("+500 DUTY")}else toast(d.message)}catch(e){toast("Server error")}}
async function ranking(){try{let r=await fetch(`${API_URL}/api/ranking`);let data=await r.json();open("<h2>🏆 Ranking</h2>"+data.map((x,i)=>`<div class=item>#${i+1} <b>${escapeHtml(x.username)}</b><small>${x.balance.toLocaleString()} DUTY</small></div>`).join(""))}catch(e){toast("Ranking unavailable")}}
async function tasks(){try{let r=await fetch(`${API_URL}/api/tasks`);let data=await r.json();open("<h2>🎯 Tasks</h2>"+data.map(x=>`<div class=item><b>${escapeHtml(x.title)}</b><small>Reward: ${x.reward} DUTY</small></div>`).join(""))}catch(e){toast("Tasks unavailable")}}
async function boost(){
  try{
    if(!initData)return toast("Open inside Telegram");

    const r=await fetch(`${API_URL}/api/boost`,{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({
        init_data:initData
      })
    });

    const d=await r.json().catch(()=>({}));

    if(!r.ok){
      throw new Error(d.detail||d.error||"Boost failed");
    }

    if(d.ok){
      if(typeof d.balance==="number")S.balance=d.balance;
      if(typeof d.tap_power==="number")S.tap_power=d.tap_power;
      render();
      toast("⚡ Tap Power upgraded!");
    }else{
      toast(d.detail||d.error||"Boost unavailable");
    }
  }catch(e){
    console.error("BOOST ERROR:", e);
toast(e.message || "Boost failed");
  }
}
function friends(){let me=tg?.initDataUnsafe?.user?.id;let link=me?`https://t.me/DutyCoinBot?start=${me}`:"Open this game inside Telegram";open(`<h2>👥 Friends</h2><p>Invite friends and build your squad.</p><div class=item><b>Your referral link</b><small>${link}</small></div><button class=wide onclick="navigator.clipboard?.writeText('${link}');toast('Copied!')">🔗 COPY LINK</button>`)}
async function wallet(){open(`<h2>💳 Wallet</h2><p>Enter only your public TON wallet address. Never enter a seed phrase or private key.</p><input id=w type=text placeholder="TON wallet address" style="width:100%;padding:13px;border-radius:12px;border:1px solid #fff2;background:#fff1;color:white"><button class=wide onclick="saveWallet()">SAVE WALLET</button>`)}
async function saveWallet(){let w=document.getElementById("w").value.trim();if(!w)return toast("Enter a wallet address");try{let r=await fetch(`${API_URL}/api/wallet`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({init_data:initData,wallet:w})});if(!r.ok)throw 0;S.wallet=w;toast("Wallet saved");$("sheet").classList.remove("open")}catch(e){toast("Could not save wallet")}}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[m]))}
document.querySelectorAll("[data-panel]").forEach(b=>b.onclick=()=>{let p=b.dataset.panel;if(p==="daily")open(`<h2>🎁 Daily Reward</h2><p>Claim 500 DUTY once every 24 hours.</p><button class=wide onclick="daily()">🎁 CLAIM 500 DUTY</button>`);if(p==="friends")friends();if(p==="ranking")ranking();if(p==="tasks")tasks();if(p==="boost")open(`<h2>⚡ Boost</h2><p>Increase Tap Power. Cost: 1,000 × current Tap Power.</p><button class=wide onclick="boost()">⚡ UPGRADE</button>`)});
$("wallet").onclick=wallet;
load();render();
