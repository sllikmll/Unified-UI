var e=null;function t(e){let t=String(e||``);return t.endsWith(`
`)?t:t+`
`}function n(e){return String(e||``).replace(/[.*+?^${}()|[\]\\]/g,`\\$&`)}function r(e,t){let r=String(e||``),i=RegExp(`^(?:${n(t)})\\s*:\\s*(.*)$`,`m`).exec(r);if(!i)return null;let a=i.index,o=r.indexOf(`
`,a),s=o===-1?r.length:o+1,c=r.slice(s),l=/^(?!\s)(?!#)([A-Za-z0-9_.-]+)\s*:/m.exec(c);return{headerStart:a,headerEnd:s,bodyStart:s,bodyEnd:l?s+l.index:r.length,inlineTail:String(i[1]||``).trim()}}function i(e,t){let r=String(e||``),i=RegExp(`^(${n(t)}\\s*:)\\s*(\\[\\]|\\{\\}|null|~)?\\s*(#.*)?$`,`m`),a=i.exec(r);if(!a)return r;let o=`${t}:${a[3]?` `+a[3].trim():``}`;return r.replace(i,o)}function a(e,n,a,o){let s=(o||{}).avoidDuplicates!==!1,c=t(String(e||``));c=i(c,n);let l=r(c,n),u=t(String(a||``)).trimEnd()+`
`;if(!l){let e=c.trimEnd().length?`
`:``;return c.trimEnd()+e+`${n}:\n`+u}if(s)try{if(c.includes(u.trim()))return c}catch{}let d=c.slice(0,l.bodyEnd),f=c.slice(l.bodyEnd),p=d;p.endsWith(`
`)||(p+=`
`);let m=c.slice(l.bodyStart,l.bodyEnd);return m.trim().length>0&&!m.endsWith(`

`)&&(p.endsWith(`
`)||(p+=`
`)),p+=u,p+f}function o(){return null}function s(){return{init:l,load:u,onShow:d,ensureNewline:t,findSection:r,insertIntoSection:a,dispose:o}}function c(){try{return e||=s(),e}catch(e){return console.error(e),null}}function l(){return c()}function u(){return c()}function d(){return c()}function f(...e){let t=c();return!t||typeof t.dispose!=`function`?null:t.dispose(...e)}Object.freeze({get:c,init:l,load:u,onShow:d,ensureNewline:t,findSection:r,insertIntoSection:a,dispose:f});export{c as t};