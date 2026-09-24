function qs(s){return document.querySelector(s)}
function money(n){return Number(n||0).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}
function todayISO(){return new Date().toLocaleDateString('en-CA',{timeZone:'America/Sao_Paulo'})}
function toast(msg,type='success'){const d=document.createElement('div');d.className='toast '+type;d.textContent=msg;document.body.appendChild(d);setTimeout(()=>d.remove(),3200)}
function csrf(){return document.querySelector('meta[name="csrf-token"]')?.content||''}
async function api(url,opt={}){const headers={'Content-Type':'application/json','X-CSRFToken':csrf(),...(opt.headers||{})};const r=await fetch(url,{...opt,headers});const j=await r.json().catch(()=>({}));if(!r.ok)throw new Error(j.error||'Erro na operação');return j}

document.addEventListener('DOMContentLoaded',()=>{
 document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab-panel').forEach(x=>x.classList.remove('active'));b.classList.add('active');qs('#'+b.dataset.tab)?.classList.add('active');localStorage.setItem('fio_tab',b.dataset.tab)})
 const saved=localStorage.getItem('fio_tab'); if(saved) document.querySelector(`.tabs button[data-tab="${saved}"]`)?.click()
 document.querySelectorAll('.segmented button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.segmented button').forEach(x=>x.classList.remove('active'));b.classList.add('active');if(qs('#tipo'))qs('#tipo').value=b.dataset.mode;qs('#adminSecond')?.classList.toggle('hidden',b.dataset.mode!=='admin')})
 ['saleDate','expenseDate','creditDate','aDate'].forEach(id=>{const e=qs('#'+id);if(e)e.value=todayISO()})
 const sale=qs('#saleService'); if(sale){sale.onchange=()=>qs('#salePrice').value=sale.selectedOptions[0].dataset.price;sale.dispatchEvent(new Event('change'))}
 const credit=qs('#creditService'); if(credit){credit.onchange=()=>qs('#creditValue').value=credit.selectedOptions[0].dataset.price;credit.dispatchEvent(new Event('change'))}
 setupAppointmentForm()
 setupAppointmentFilters()
 setupProfessionalCalendar()
 const paySelect=qs('#payCreditSelect'); if(paySelect){paySelect.addEventListener('change',updatePayCreditInfo); updatePayCreditInfo()}
})

function openModal(id){qs('#'+id)?.classList.add('show')}
function closeModal(id){qs('#'+id)?.classList.remove('show')}

async function saveGoal(){try{const goal=Number(qs('#goalInput').value);if(goal<0)throw Error('Meta inválida');await api('/api/goal',{method:'POST',body:JSON.stringify({goal})});toast('Meta salva!');location.reload()}catch(e){toast(e.message,'error')}}

async function saveSale(){try{const v=Number(qs('#salePrice').value);if(v<0)throw Error('Informe um valor válido');await api('/api/flow',{method:'POST',body:JSON.stringify({tipo:'Entrada',descricao:'Atendimento: '+qs('#saleService').value,valor:v,data:qs('#saleDate').value})});toast('Atendimento registrado!');location.reload()}catch(e){toast(e.message,'error')}}
async function saveExpense(){try{const v=Number(qs('#expenseValue').value);const desc=qs('#expenseDesc').value.trim();if(v<=0||!desc)throw Error('Informe descrição e valor válidos');await api('/api/flow',{method:'POST',body:JSON.stringify({tipo:'Saída',descricao:desc,valor:-v,data:qs('#expenseDate').value})});toast('Despesa lançada!');location.reload()}catch(e){toast(e.message,'error')}}
async function saveCredit(){try{const name=qs('#creditName').value.trim();const v=Number(qs('#creditValue').value);if(!name||v<=0)throw Error('Informe cliente e valor');await api('/api/flow',{method:'POST',body:JSON.stringify({tipo:'Pendência',descricao:'Fiado de: '+name+' ('+qs('#creditService').value+')',valor:v,data:qs('#creditDate').value})});toast('Fiado registrado!');location.reload()}catch(e){toast(e.message,'error')}}
async function deleteFlow(id){if(!confirm('Excluir esta movimentação?'))return;try{await api('/api/flow?id='+id,{method:'DELETE'});location.reload()}catch(e){toast(e.message,'error')}}
async function payCredit(id){if(!confirm('Baixar este fiado como recebido?'))return;try{await api('/api/flow/'+id+'/pay',{method:'POST'});toast('Fiado baixado!');location.reload()}catch(e){toast(e.message,'error')}}

async function appointmentAction(id,action){
 const labels={confirm:'Confirmar este agendamento?',cancel:'Cancelar este agendamento?',complete:'Registrar atendimento e receber R$ do cliente?',fiado:'Concluir atendimento como fiado?'};
 if(!confirm(labels[action]||'Confirmar ação?'))return;
 try{const r=await api('/api/appointments/'+id,{method:'POST',body:JSON.stringify({action})});
  const msg=action==='confirm'?'Agendamento confirmado!':action==='complete'?'Atendimento concluído e lançado no caixa!':action==='fiado'?'Atendimento concluído como fiado!':'Agendamento cancelado!';
  toast(msg);setTimeout(()=>location.reload(),350);
 }catch(e){toast(e.message,'error')}
}


let editingService='__new__';
function editService(oldName,price){editingService=oldName;qs('#serviceEditorTitle').textContent=oldName==='__new__'?'Adicionar serviço':'Editar serviço';qs('#serviceName').value=oldName==='__new__'?'':oldName;qs('#servicePrice').value=oldName==='__new__'?'':price;qs('#serviceName').focus()}
async function saveService(){try{const name=qs('#serviceName').value.trim(),price=Number(qs('#servicePrice').value);if(!name||price<0)throw Error('Informe nome e preço válidos');await api('/api/services',{method:'POST',body:JSON.stringify({old:editingService,name,price})});toast('Serviço salvo!');location.reload()}catch(e){toast(e.message,'error')}}
function deleteService(name){if(!confirm('Excluir '+name+'?'))return;api('/api/services?name='+encodeURIComponent(name),{method:'DELETE'}).then(()=>location.reload()).catch(e=>toast(e.message,'error'))}

function openPayModal(){const modal=qs('#payCreditModal');if(!modal)return;openModal('payCreditModal');updatePayCreditInfo()}
function updatePayCreditInfo(){const s=qs('#payCreditSelect'),info=qs('#payCreditInfo');if(!s||!info)return;const v=Number(s.selectedOptions[0]?.dataset.value||0);info.textContent='Valor a receber: R$ '+money(v);}
async function paySelectedCredit(){const s=qs('#payCreditSelect');if(!s||!s.value)return toast('Selecione um fiado.','error');const id=Number(s.value);if(!confirm('Confirmar recebimento deste fiado?'))return;try{await api('/api/flow/'+id+'/pay',{method:'POST'});toast('Fiado marcado como pago!');closeModal('payCreditModal');location.reload()}catch(e){toast(e.message,'error')}}

async function createMonthly(){try{if(!qs('#mName').value.trim())throw Error('Informe o nome');await api('/api/monthly',{method:'POST',body:JSON.stringify({action:'create',name:qs('#mName').value,phone:qs('#mPhone').value})});location.reload()}catch(e){toast(e.message,'error')}}
async function addMonthlyService(){try{const price=Number(qs('#mPrice').value),qty=Number(qs('#mQty').value);if(price<0||qty<1)throw Error('Dados inválidos');await api('/api/monthly',{method:'POST',body:JSON.stringify({action:'service',id:Number(qs('#mClient').value),qty,price})});location.reload()}catch(e){toast(e.message,'error')}}
async function payMonthly(id,max){const v=prompt('Valor a receber (máx. R$ '+money(max)+'):',max);if(v===null)return;const n=Number(v);if(n<=0||n>max)return toast('Valor inválido','error');try{await api('/api/monthly',{method:'POST',body:JSON.stringify({action:'pay',id,value:n})});location.reload()}catch(e){toast(e.message,'error')}}

function copyBooking(){const e=qs('#bookingLink');navigator.clipboard.writeText(e.value).then(()=>toast('Link copiado!')).catch(()=>{e.select();document.execCommand('copy');toast('Link copiado!')})}
async function shareBooking(){const url=qs('#bookingLink')?.value||window.APP?.bookingLink;if(navigator.share){try{await navigator.share({title:'Agendamento',text:'Agende seu horário online:',url})}catch(e){}}else{copyBooking()}}

function setupBooking(salao){const d=qs('#bookingDate'),h=qs('#bookingHour'),btn=qs('#bookingSubmit');if(!d)return;async function load(){if(!d.value)return;h.innerHTML='<option>Carregando...</option>';if(btn)btn.disabled=true;try{const r=await fetch('/api/booking/slots?salao='+encodeURIComponent(salao)+'&date='+d.value);const slots=await r.json();h.innerHTML=slots.length?'<option value="">Selecione</option>'+slots.map(x=>`<option value="${x}">${x}</option>`).join(''):'<option value="">Sem horários disponíveis</option>'}catch{h.innerHTML='<option value="">Erro ao carregar</option>'}finally{if(btn)btn.disabled=false}}d.addEventListener('change',load);if(d.value)load()}

function setupAppointmentForm(){const d=qs('#aDate'),h=qs('#aHour');if(!d||!h)return;async function load(){if(!d.value)return;h.innerHTML='<option>Carregando...</option>';try{const r=await fetch('/api/booking/slots?salao='+encodeURIComponent(window.APP?.user||'')+'&date='+d.value);const slots=await r.json();h.innerHTML=slots.length?'<option value="">Selecione</option>'+slots.map(x=>`<option value="${x}">${x}</option>`).join(''):'<option value="">Sem horários</option>'}catch{h.innerHTML='<option value="">Erro</option>'}}d.addEventListener('change',load)}

async function createAppointment(){try{const data={nome:qs('#aName').value.trim(),telefone:qs('#aPhone').value,servico:qs('#aService').value,data:qs('#aDate').value,hora:qs('#aHour').value};if(!data.nome||!data.data||!data.hora)throw Error('Preencha os dados do agendamento');await api('/api/appointments',{method:'POST',body:JSON.stringify(data)});toast('Agendamento criado!');closeModal('appointmentModal');location.reload()}catch(e){toast(e.message,'error')}}

function setupAppointmentFilters(){
 const buttons=document.querySelectorAll('[data-appt-filter]');if(!buttons.length)return;
 buttons.forEach(b=>b.onclick=()=>{
  buttons.forEach(x=>x.classList.remove('active'));b.classList.add('active');
  const rows=document.querySelectorAll('#appointmentList .appointment');
  rows.forEach(row=>{const date=row.dataset.date;const show=b.dataset.apptFilter==='all'||(b.dataset.apptFilter==='today'&&date===todayISO());row.style.display=show?'flex':'none'});
  if(b.dataset.apptFilter==='today') selectCalendarDay(todayISO());
 });
}

let calendarMonth=new Date();calendarMonth.setDate(1);let selectedCalendarDate=todayISO();
function isoDate(y,m,d){return `${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`}
function changeCalendar(delta){calendarMonth.setMonth(calendarMonth.getMonth()+delta);renderCalendar()}
function selectCalendarDay(date){
 selectedCalendarDate=date;
 renderCalendar();
 document.querySelectorAll('#appointmentList .appointment').forEach(row=>row.style.display=row.dataset.date===date?'flex':'none');
 const title=qs('#selectedDayTitle'),sub=qs('#selectedDaySubtitle');
 if(title){const [y,m,d]=date.split('-');title.textContent=`Agendamentos de ${d}/${m}/${y}`;}
 if(sub){const n=(window.APP?.appointments||[]).filter(a=>a.Data===date).length;sub.textContent=n?`${n} agendamento(s) neste dia.`:'Nenhum agendamento neste dia.'}
 document.querySelectorAll('[data-appt-filter]').forEach(x=>x.classList.remove('active'));
}
function setupProfessionalCalendar(){
 if(!qs('#calendarGrid'))return;
 renderCalendar();selectCalendarDay(selectedCalendarDate);
}
function renderCalendar(){
 const grid=qs('#calendarGrid'),title=qs('#calendarTitle'),subtitle=qs('#calendarSubtitle');if(!grid)return;
 const y=calendarMonth.getFullYear(),m=calendarMonth.getMonth();
 const monthName=calendarMonth.toLocaleDateString('pt-BR',{month:'long',year:'numeric'});
 if(title)title.textContent=monthName.charAt(0).toUpperCase()+monthName.slice(1);
 if(subtitle)subtitle.textContent='Toque em um dia para ver os horários';
 const first=new Date(y,m,1);let start=(first.getDay()+6)%7;const days=new Date(y,m+1,0).getDate();const prevDays=new Date(y,m,0).getDate();
 const appts=window.APP?.appointments||[];let html='';
 for(let i=0;i<start;i++){const d=prevDays-start+i+1;html+=`<div class="calendar-day muted"><span class="day-number">${d}</span></div>`}
 for(let d=1;d<=days;d++){
  const date=isoDate(y,m,d);const list=appts.filter(a=>a.Data===date);const isToday=date===todayISO();const selected=date===selectedCalendarDate;
  html+=`<button type="button" class="calendar-day ${isToday?'today ':''}${selected?'selected':''}" onclick="selectCalendarDay('${date}')"><span class="day-number">${d}</span>${list.length?`<span class="day-count">${list.length} ${list.length===1?'horário':'horários'}</span><i class="dot"></i>`:''}</button>`;
 }
 const total=start+days;const tail=(7-(total%7))%7;for(let d=1;d<=tail;d++)html+=`<div class="calendar-day muted"><span class="day-number">${d}</span></div>`;
 grid.innerHTML=html;
}
