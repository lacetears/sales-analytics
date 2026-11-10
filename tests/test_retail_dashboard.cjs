// Execute the actual generated script with a minimal DOM, not a browser visual test.
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict'), path=require('node:path');
const elements=new Map();
function element(){return {value:'',textContent:'',style:{},children:[],append(...xs){this.children.push(...xs)},replaceChildren(){this.children=[]}}}
const document={getElementById(id){if(!elements.has(id)) elements.set(id,element());return elements.get(id)},createElement:element};
const html=fs.readFileSync(path.join(__dirname,'../retail/output/dashboard.html'),'utf8');
const context=vm.createContext({document,Intl,Set,console});
vm.runInContext(html.match(/<script>([\s\S]*)<\/script>/)[1],context);
const report=JSON.parse(fs.readFileSync(path.join(__dirname,'../retail/output/report.json'),'utf8'));
const money=n=>new Intl.NumberFormat('en-GB',{style:'currency',currency:'GBP',maximumFractionDigits:2}).format(n/100);
assert.equal(document.getElementById('net').textContent,money(report.totals.net_pence));
assert.equal(document.getElementById('quality').children.length,Object.keys(report.quality).length);
for(const [country,month] of [['United Kingdom','2011-12'],['USA','2011-04'],['Missing','']]){
 document.getElementById('country').value=country;document.getElementById('month').value=month;
 vm.runInContext('render()',context);
 const selected=report.monthly_country.filter(r=>r.country===country&&(!month||r.month===month));
 assert.equal(document.getElementById('net').textContent,money(selected.reduce((s,r)=>s+r.net_pence,0)));
 assert.equal(document.getElementById('products').children.length,report.products.length);
}
console.log('Retail dashboard: source totals, quality counts, combined filters, negative slice, empty slice and fixed product table passed.');
