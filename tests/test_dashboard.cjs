// Dependency-free check of the generated dashboard script and filter behavior.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const elements = new Map();
function element() { return {value: '', textContent: '', innerHTML: '', children: [], append(child) {this.children.push(child)}, addEventListener() {}}; }
const document = {getElementById(id) {if (!elements.has(id)) elements.set(id, element()); return elements.get(id)}, createElement: element};
const html = fs.readFileSync(path.join(__dirname, '../data-analytics/output/dashboard.html'), 'utf8');
const script = html.match(/<script>([\s\S]*)<\/script>/)[1];
const context = vm.createContext({document, Intl, Date, Set, console});
vm.runInContext(script, context);
assert.equal(document.getElementById('revenue').textContent, '$1,014,041');
assert.equal(document.getElementById('region').children.length, 4);
const allOrders = document.getElementById('orders').textContent;
document.getElementById('region').value = 'North';
document.getElementById('product').value = 'Laptop';
vm.runInContext('render()', context);
assert.ok(document.getElementById('orders').textContent < allOrders);
assert.ok(document.getElementById('products').innerHTML.includes('Laptop'));
assert.ok(!document.getElementById('products').innerHTML.includes('Monitor'));
const expected = vm.runInContext("data.filter(r=>r.region==='North'&&r.product==='Laptop'&&r.status==='Completed').reduce((s,r)=>s+r.net_revenue_cents,0)", context);
assert.equal(document.getElementById('revenue').textContent, new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(expected/100));
document.getElementById('region').value = 'Missing';
vm.runInContext('render()', context);
assert.equal(document.getElementById('margin').textContent, '—');
assert.equal(document.getElementById('revenue').textContent, '$0');
console.log('Dashboard totals, combined filters, product table, and empty selection passed.');
