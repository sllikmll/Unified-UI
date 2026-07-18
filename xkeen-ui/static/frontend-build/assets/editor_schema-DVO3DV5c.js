import{a as e,c as t,i as n,l as r,o as i,t as a}from"./yaml_schema-CZjJUoY_.js";import{a as o,i as s,n as c,o as l,r as u,s as d}from"./codemirror_json_schema-DTKqfgOM.js";import{modify as f}from"jsonc-parser";import{dump as p,load as m}from"js-yaml";var h=`На Keenetic Xray DNS обычно настраивают по инструкции https://jameszero.net/3398.htm: вместе с dns-out outbound, routing rules для портa 53 и domainStrategy на proxy/direct.`,ee=`На Keenetic DNS-блок Mihomo редко используется напрямую: обычно требует перенастройки системного резолвера и firewall, иначе ломается разрешение имён для самого роутера.`,g=`На Keenetic TUN-блок Mihomo редко используется: требует включения TUN-режима в прошивке и корректных ip-rules/route таблиц, иначе роутер не маршрутизирует трафик.`,te=[{id:`xray-rule-block-domain`,label:`rule: block by domain`,detail:`Xray · routing.rules[]`,documentation:`Правило блокировки трафика к указанным доменам. Поддерживает exact-домены и ссылки geosite:*.`,insertText:`{
  "type": "field",
  "domain": [
    "geosite:category-ads-all"
  ],
  "outboundTag": "block"
}`,monacoSnippet:`{
  "type": "field",
  "domain": [
    "\${1:geosite:category-ads-all}"
  ],
  "outboundTag": "\${2:block}"
}$0`},{id:`xray-rule-block-ip`,label:`rule: block by IP / CIDR`,detail:`Xray · routing.rules[]`,documentation:`Блокировка трафика на IP, CIDR или geoip:*.`,insertText:`{
  "type": "field",
  "ip": [
    "geoip:private"
  ],
  "outboundTag": "block"
}`,monacoSnippet:`{
  "type": "field",
  "ip": [
    "\${1:geoip:private}"
  ],
  "outboundTag": "\${2:block}"
}$0`},{id:`xray-rule-block-quic`,label:`rule: block QUIC`,detail:`Xray В· routing.rules[]`,documentation:`Блокировка QUIC в Xray через правило для UDP/443. Обычно такое правило ставят выше общих proxy/direct rules.`,insertText:`{
  "type": "field",
  "network": "udp",
  "port": "443",
  "outboundTag": "block"
}`,monacoSnippet:`{
  "type": "field",
  "network": "udp",
  "port": "\${1:443}",
  "outboundTag": "\${2:block}"
}$0`},{id:`xray-rule-proxy-domain`,label:`rule: proxy by domain`,detail:`Xray · routing.rules[]`,documentation:`Направить трафик по списку доменов через proxy/balancer outbound.`,insertText:`{
  "type": "field",
  "domain": [
    "geosite:geolocation-!cn"
  ],
  "outboundTag": "proxy"
}`,monacoSnippet:`{
  "type": "field",
  "domain": [
    "\${1:geosite:geolocation-!cn}"
  ],
  "outboundTag": "\${2:proxy}"
}$0`},{id:`xray-rule-direct-domain`,label:`rule: direct by domain`,detail:`Xray · routing.rules[]`,documentation:`Пропустить трафик напрямую (freedom) по списку доменов.`,insertText:`{
  "type": "field",
  "domain": [
    "geosite:private",
    "geosite:ru"
  ],
  "outboundTag": "direct"
}`,monacoSnippet:`{
  "type": "field",
  "domain": [
    "\${1:geosite:private}",
    "\${2:geosite:ru}"
  ],
  "outboundTag": "\${3:direct}"
}$0`},{id:`xray-rule-proxy-by-port`,label:`rule: proxy by port`,detail:`Xray · routing.rules[]`,documentation:`Проксировать трафик по port/port-range (например TCP 443, UDP 443 — QUIC).`,insertText:`{
  "type": "field",
  "network": "tcp,udp",
  "port": "443",
  "outboundTag": "proxy"
}`,monacoSnippet:`{
  "type": "field",
  "network": "\${1|tcp,udp,tcp,udp|}",
  "port": "\${2:443}",
  "outboundTag": "\${3:proxy}"
}$0`},{id:`xray-rule-proxy-by-process`,label:`rule: proxy by process name`,detail:`Xray · routing.rules[]`,documentation:`Проксировать трафик конкретного процесса (по имени исполняемого файла).`,insertText:`{
  "type": "field",
  "process": [
    "chrome.exe"
  ],
  "outboundTag": "proxy"
}`,monacoSnippet:`{
  "type": "field",
  "process": [
    "\${1:chrome.exe}"
  ],
  "outboundTag": "\${2:proxy}"
}$0`},{id:`xray-rule-via-balancer`,label:`rule: route via balancer`,detail:`Xray · routing.rules[]`,documentation:`Направить трафик в balancer вместо конкретного outbound.`,insertText:`{
  "type": "field",
  "domain": [
    "geosite:geolocation-!cn"
  ],
  "balancerTag": "balancer-auto"
}`,monacoSnippet:`{
  "type": "field",
  "domain": [
    "\${1:geosite:geolocation-!cn}"
  ],
  "balancerTag": "\${2:balancer-auto}"
}$0`}],ne=[{id:`xray-balancer-auto`,label:`balancer: auto (observatory)`,detail:`Xray · routing.balancers[]`,documentation:`Автоматический balancer с observatory-стратегией. На Keenetic осторожно с количеством селекторов — 300+ узлов кладут роутер.`,insertText:`{
  "tag": "balancer-auto",
  "selector": [
    "proxy-"
  ],
  "strategy": {
    "type": "leastPing"
  }
}`,monacoSnippet:`{
  "tag": "\${1:balancer-auto}",
  "selector": [
    "\${2:proxy-}"
  ],
  "strategy": {
    "type": "\${3|leastPing,random,roundRobin,leastLoad|}"
  }
}$0`},{id:`xray-balancer-leastload`,label:`balancer: leastLoad`,detail:`Xray · routing.balancers[]`,documentation:`Balancer с leastLoad — использует observatory-метрики для выбора наименее загруженного исходящего.`,insertText:`{
  "tag": "balancer-leastload",
  "selector": [
    "proxy-"
  ],
  "strategy": {
    "type": "leastLoad",
    "settings": {
      "baselines": [
        "300ms",
        "500ms"
      ],
      "expected": 2
    }
  }
}`,monacoSnippet:`{
  "tag": "\${1:balancer-leastload}",
  "selector": [
    "\${2:proxy-}"
  ],
  "strategy": {
    "type": "leastLoad",
    "settings": {
      "baselines": [
        "\${3:300ms}",
        "\${4:500ms}"
      ],
      "expected": \${5:2}
    }
  }
}$0`}],re=[{id:`xray-outbound-direct`,label:`outbound: direct (freedom)`,detail:`Xray · outbounds[]`,documentation:`Прямой исходящий — freedom protocol. Обычный tag: "direct".`,insertText:`{
  "tag": "direct",
  "protocol": "freedom",
  "settings": {
    "domainStrategy": "UseIPv4"
  }
}`,monacoSnippet:`{
  "tag": "\${1:direct}",
  "protocol": "freedom",
  "settings": {
    "domainStrategy": "\${2|UseIPv4,UseIP,UseIPv6,AsIs|}"
  }
}$0`},{id:`xray-outbound-block`,label:`outbound: block (blackhole)`,detail:`Xray · outbounds[]`,documentation:`Блокирующий исходящий — blackhole protocol. Используется с outboundTag: "block" в rules.`,insertText:`{
  "tag": "block",
  "protocol": "blackhole",
  "settings": {
    "response": {
      "type": "http"
    }
  }
}`,monacoSnippet:`{
  "tag": "\${1:block}",
  "protocol": "blackhole",
  "settings": {
    "response": {
      "type": "\${2|http,none|}"
    }
  }
}$0`},{id:`xray-outbound-vless-reality`,label:`outbound: VLESS Reality`,detail:`Xray · outbounds[]`,documentation:`VLESS-исходящий с Reality-транспортом. Подставь реальные address, id, serverName, publicKey, shortId.`,insertText:`{
  "tag": "proxy-reality",
  "protocol": "vless",
  "settings": {
    "address": "example.com",
    "port": 443,
    "id": "00000000-0000-0000-0000-000000000000",
    "encryption": "none",
    "flow": "xtls-rprx-vision"
  },
  "streamSettings": {
    "network": "tcp",
    "security": "reality",
    "realitySettings": {
      "serverName": "example.com",
      "fingerprint": "chrome",
      "publicKey": "",
      "shortId": ""
    }
  }
}`,monacoSnippet:`{
  "tag": "\${1:proxy-reality}",
  "protocol": "vless",
  "settings": {
    "address": "\${2:example.com}",
    "port": \${3:443},
    "id": "\${4:00000000-0000-0000-0000-000000000000}",
    "encryption": "none",
    "flow": "\${5|xtls-rprx-vision,|}"
  },
  "streamSettings": {
    "network": "tcp",
    "security": "reality",
    "realitySettings": {
      "serverName": "\${6:example.com}",
      "fingerprint": "\${7|chrome,firefox,safari,edge,ios,android,random|}",
      "publicKey": "\${8}",
      "shortId": "\${9}"
    }
  }
}$0`},{id:`xray-outbound-vless-xhttp`,label:`outbound: VLESS XHTTP`,detail:`Xray · outbounds[]`,documentation:`VLESS-исходящий через XHTTP-транспорт (современный замен ws/grpc в ряде сценариев).`,insertText:`{
  "tag": "proxy-xhttp",
  "protocol": "vless",
  "settings": {
    "address": "example.com",
    "port": 443,
    "id": "00000000-0000-0000-0000-000000000000",
    "encryption": "none"
  },
  "streamSettings": {
    "network": "xhttp",
    "security": "tls",
    "tlsSettings": {
      "serverName": "example.com",
      "alpn": ["h2"]
    },
    "xhttpSettings": {
      "host": "example.com",
      "path": "/",
      "mode": "stream-one"
    }
  }
}`,monacoSnippet:`{
  "tag": "\${1:proxy-xhttp}",
  "protocol": "vless",
  "settings": {
    "address": "\${2:example.com}",
    "port": \${3:443},
    "id": "\${4:00000000-0000-0000-0000-000000000000}",
    "encryption": "none"
  },
  "streamSettings": {
    "network": "xhttp",
    "security": "tls",
    "tlsSettings": {
      "serverName": "\${5:example.com}",
      "alpn": ["h2"]
    },
    "xhttpSettings": {
      "host": "\${6:example.com}",
      "path": "\${7:/}",
      "mode": "\${8|stream-one,packet-up,stream-up|}"
    }
  }
}$0`},{id:`xray-outbound-trojan`,label:`outbound: Trojan`,detail:`Xray · outbounds[]`,documentation:`Trojan-исходящий через TLS. Простая замена Shadowsocks c TLS-маскировкой.`,insertText:`{
  "tag": "proxy-trojan",
  "protocol": "trojan",
  "settings": {
    "servers": [
      {
        "address": "example.com",
        "port": 443,
        "password": "your-password"
      }
    ]
  },
  "streamSettings": {
    "network": "tcp",
    "security": "tls",
    "tlsSettings": {
      "serverName": "example.com"
    }
  }
}`,monacoSnippet:`{
  "tag": "\${1:proxy-trojan}",
  "protocol": "trojan",
  "settings": {
    "servers": [
      {
        "address": "\${2:example.com}",
        "port": \${3:443},
        "password": "\${4:your-password}"
      }
    ]
  },
  "streamSettings": {
    "network": "tcp",
    "security": "tls",
    "tlsSettings": {
      "serverName": "\${5:example.com}"
    }
  }
}$0`},{id:`xray-outbound-shadowsocks`,label:`outbound: Shadowsocks`,detail:`Xray · outbounds[]`,documentation:`Shadowsocks-исходящий. Для современных серверов используй 2022-шифры.`,insertText:`{
  "tag": "proxy-ss",
  "protocol": "shadowsocks",
  "settings": {
    "servers": [
      {
        "address": "example.com",
        "port": 8388,
        "method": "2022-blake3-aes-128-gcm",
        "password": "your-password"
      }
    ]
  }
}`,monacoSnippet:`{
  "tag": "\${1:proxy-ss}",
  "protocol": "shadowsocks",
  "settings": {
    "servers": [
      {
        "address": "\${2:example.com}",
        "port": \${3:8388},
        "method": "\${4|2022-blake3-aes-128-gcm,2022-blake3-aes-256-gcm,aes-128-gcm,aes-256-gcm,chacha20-poly1305|}",
        "password": "\${5:your-password}"
      }
    ]
  }
}$0`}],ie=[{id:`xray-inbound-socks`,label:`inbound: socks`,detail:`Xray · inbounds[]`,documentation:`Socks5-входящий без авторизации, слушает локально. udp: true нужен для QUIC/UDP-трафика.`,insertText:`{
  "tag": "socks-in",
  "listen": "127.0.0.1",
  "port": 10808,
  "protocol": "socks",
  "settings": {
    "auth": "noauth",
    "udp": true
  },
  "sniffing": {
    "enabled": true,
    "destOverride": ["http", "tls", "quic"]
  }
}`,monacoSnippet:`{
  "tag": "\${1:socks-in}",
  "listen": "\${2:127.0.0.1}",
  "port": \${3:10808},
  "protocol": "socks",
  "settings": {
    "auth": "\${4|noauth,password|}",
    "udp": \${5|true,false|}
  },
  "sniffing": {
    "enabled": true,
    "destOverride": ["http", "tls", "quic"]
  }
}$0`},{id:`xray-inbound-http`,label:`inbound: http`,detail:`Xray · inbounds[]`,documentation:`HTTP-прокси входящий. Полезен для браузеров, не поддерживающих SOCKS5.`,insertText:`{
  "tag": "http-in",
  "listen": "127.0.0.1",
  "port": 10809,
  "protocol": "http",
  "settings": {
    "allowTransparent": false
  }
}`,monacoSnippet:`{
  "tag": "\${1:http-in}",
  "listen": "\${2:127.0.0.1}",
  "port": \${3:10809},
  "protocol": "http",
  "settings": {
    "allowTransparent": false
  }
}$0`},{id:`xray-inbound-dokodemo`,label:`inbound: dokodemo-door (transparent)`,detail:`Xray · inbounds[]`,documentation:`Transparent-входящий для iptables REDIRECT / TPROXY. На Keenetic — для перехвата трафика LAN.`,insertText:`{
  "tag": "transparent-in",
  "listen": "0.0.0.0",
  "port": 12345,
  "protocol": "dokodemo-door",
  "settings": {
    "network": "tcp,udp",
    "followRedirect": true
  },
  "streamSettings": {
    "sockopt": {
      "tproxy": "tproxy"
    }
  },
  "sniffing": {
    "enabled": true,
    "destOverride": ["http", "tls", "quic"]
  }
}`,monacoSnippet:`{
  "tag": "\${1:transparent-in}",
  "listen": "\${2:0.0.0.0}",
  "port": \${3:12345},
  "protocol": "dokodemo-door",
  "settings": {
    "network": "tcp,udp",
    "followRedirect": true
  },
  "streamSettings": {
    "sockopt": {
      "tproxy": "\${4|tproxy,redirect,off|}"
    }
  },
  "sniffing": {
    "enabled": true,
    "destOverride": ["http", "tls", "quic"]
  }
}$0`}],_=[{id:`xray-stream-ws`,label:`streamSettings: WebSocket`,detail:`Xray · streamSettings`,documentation:`WebSocket-транспорт для VLESS/VMess/Trojan. Часто используется за CDN.`,insertText:`"network": "ws",
"wsSettings": {
  "path": "/",
  "headers": {
    "Host": "example.com"
  }
}`,monacoSnippet:`"network": "ws",
"wsSettings": {
  "path": "\${1:/}",
  "headers": {
    "Host": "\${2:example.com}"
  }
}$0`},{id:`xray-stream-grpc`,label:`streamSettings: gRPC`,detail:`Xray · streamSettings`,documentation:`gRPC-транспорт. Требует TLS и совпадающий serviceName на клиенте/сервере.`,insertText:`"network": "grpc",
"grpcSettings": {
  "serviceName": "xray-svc",
  "multiMode": false
}`,monacoSnippet:`"network": "grpc",
"grpcSettings": {
  "serviceName": "\${1:xray-svc}",
  "multiMode": \${2|false,true|}
}$0`},{id:`xray-stream-xhttp`,label:`streamSettings: XHTTP`,detail:`Xray · streamSettings`,documentation:`XHTTP-транспорт (новое поколение). Mode stream-one обычно ок для browser-traffic, packet-up — для UDP-like нагрузок.`,insertText:`"network": "xhttp",
"xhttpSettings": {
  "host": "example.com",
  "path": "/",
  "mode": "stream-one"
}`,monacoSnippet:`"network": "xhttp",
"xhttpSettings": {
  "host": "\${1:example.com}",
  "path": "\${2:/}",
  "mode": "\${3|stream-one,packet-up,stream-up|}"
}$0`},{id:`xray-stream-tcp-http`,label:`streamSettings: TCP+HTTP obfuscation`,detail:`Xray · streamSettings`,documentation:`Raw TCP с HTTP-заголовками для обхода DPI. Устаревает в пользу XHTTP, но ещё встречается.`,insertText:`"network": "tcp",
"tcpSettings": {
  "header": {
    "type": "http",
    "request": {
      "path": ["/"],
      "headers": {
        "Host": ["example.com"]
      }
    }
  }
}`,monacoSnippet:`"network": "tcp",
"tcpSettings": {
  "header": {
    "type": "http",
    "request": {
      "path": ["\${1:/}"],
      "headers": {
        "Host": ["\${2:example.com}"]
      }
    }
  }
}$0`}],ae=[{id:`xray-config-dns`,label:`dns block (Keenetic — по инструкции)`,detail:`Xray · config.dns`,documentation:`DNS-блок Xray для DNS-over-VLESS сценария. На Keenetic обычно используется вместе с dns-out outbound, routing rules для port 53/dns-in и domainStrategy на proxy/direct.`,warning:h,insertText:`"dns": {
  "tag": "dns-in",
  "servers": [
    "8.8.8.8"
  ],
  "queryStrategy": "UseIP"
}`,monacoSnippet:`"dns": {
  "tag": "\${1:dns-in}",
  "servers": [
    "\${2:8.8.8.8}"
  ],
  "queryStrategy": "\${3|UseIP,UseIPv4,UseIPv6|}"
}$0`},{id:`xray-config-observatory`,label:`observatory block`,detail:`Xray · config.observatory`,documentation:`Observatory — фоновое тестирование outbounds для balancer leastPing/leastLoad. Осторожно с числом subjectSelector — чем больше outbounds, тем выше нагрузка на роутер.`,insertText:`"observatory": {
  "subjectSelector": [
    "proxy-"
  ],
  "probeUrl": "http://www.gstatic.com/generate_204",
  "probeInterval": "5m"
}`,monacoSnippet:`"observatory": {
  "subjectSelector": [
    "\${1:proxy-}"
  ],
  "probeUrl": "\${2:http://www.gstatic.com/generate_204}",
  "probeInterval": "\${3:5m}"
}$0`},{id:`xray-config-observatory-balancer`,label:`observatory + balancer scaffold`,detail:`Xray · observatory + routing`,documentation:`Полный scaffold для leastPing-маршрутизации: observatory, balancer и базовое rule через balancerTag.`,insertText:`"observatory": {
  "subjectSelector": [
    "proxy-"
  ],
  "probeUrl": "http://www.gstatic.com/generate_204",
  "probeInterval": "5m"
},
"routing": {
  "balancers": [
    {
      "tag": "balancer-auto",
      "selector": [
        "proxy-"
      ],
      "strategy": {
        "type": "leastPing"
      },
      "fallbackTag": "direct"
    }
  ],
  "rules": [
    {
      "type": "field",
      "domain": [
        "geosite:geolocation-!cn"
      ],
      "balancerTag": "balancer-auto"
    }
  ]
}`,monacoSnippet:`"observatory": {
  "subjectSelector": [
    "\${1:proxy-}"
  ],
  "probeUrl": "\${2:http://www.gstatic.com/generate_204}",
  "probeInterval": "\${3:5m}"
},
"routing": {
  "balancers": [
    {
      "tag": "\${4:balancer-auto}",
      "selector": [
        "\${5:proxy-}"
      ],
      "strategy": {
        "type": "\${6|leastPing,leastLoad,random,roundRobin|}"
      },
      "fallbackTag": "\${7:direct}"
    }
  ],
  "rules": [
    {
      "type": "field",
      "domain": [
        "\${8:geosite:geolocation-!cn}"
      ],
      "balancerTag": "\${4:balancer-auto}"
    }
  ]
}$0`}],oe=[{id:`mihomo-proxy-vless`,label:`proxy: vless`,detail:`Mihomo · proxies[]`,documentation:`VLESS-прокси через TLS. flow xtls-rprx-vision совместим с Xray Reality.`,insertText:`name: "vless-proxy"
type: vless
server: example.com
port: 443
uuid: "00000000-0000-0000-0000-000000000000"
network: tcp
tls: true
servername: example.com
flow: xtls-rprx-vision
udp: true`,monacoSnippet:`name: "\${1:vless-proxy}"
type: vless
server: \${2:example.com}
port: \${3:443}
uuid: "\${4:00000000-0000-0000-0000-000000000000}"
network: \${5|tcp,ws,grpc|}
tls: true
servername: \${6:example.com}
flow: \${7|xtls-rprx-vision,|}
udp: true$0`},{id:`mihomo-proxy-vmess`,label:`proxy: vmess`,detail:`Mihomo · proxies[]`,documentation:`VMess-прокси. Часто используется с ws+tls за CDN.`,insertText:`name: "vmess-proxy"
type: vmess
server: example.com
port: 443
uuid: "00000000-0000-0000-0000-000000000000"
alterId: 0
cipher: auto
network: ws
tls: true
servername: example.com
ws-opts:
  path: /
  headers:
    Host: example.com
udp: true`,monacoSnippet:`name: "\${1:vmess-proxy}"
type: vmess
server: \${2:example.com}
port: \${3:443}
uuid: "\${4:00000000-0000-0000-0000-000000000000}"
alterId: \${5:0}
cipher: \${6|auto,aes-128-gcm,chacha20-poly1305,none|}
network: ws
tls: true
servername: \${7:example.com}
ws-opts:
  path: \${8:/}
  headers:
    Host: \${9:example.com}
udp: true$0`},{id:`mihomo-proxy-trojan`,label:`proxy: trojan`,detail:`Mihomo · proxies[]`,documentation:`Trojan-прокси через TLS. Минимальные поля — server/port/password/sni.`,insertText:`name: "trojan-proxy"
type: trojan
server: example.com
port: 443
password: "your-password"
sni: example.com
udp: true`,monacoSnippet:`name: "\${1:trojan-proxy}"
type: trojan
server: \${2:example.com}
port: \${3:443}
password: "\${4:your-password}"
sni: \${5:example.com}
udp: true$0`},{id:`mihomo-proxy-ss`,label:`proxy: shadowsocks`,detail:`Mihomo · proxies[]`,documentation:`Shadowsocks-прокси. Поддерживает 2022-шифры и AEAD.`,insertText:`name: "ss-proxy"
type: ss
server: example.com
port: 8388
cipher: 2022-blake3-aes-128-gcm
password: "your-password"
udp: true`,monacoSnippet:`name: "\${1:ss-proxy}"
type: ss
server: \${2:example.com}
port: \${3:8388}
cipher: \${4|2022-blake3-aes-128-gcm,2022-blake3-aes-256-gcm,aes-128-gcm,aes-256-gcm,chacha20-ietf-poly1305|}
password: "\${5:your-password}"
udp: true$0`},{id:`mihomo-proxy-openvpn`,label:`proxy: openvpn`,detail:`Mihomo · proxies[]`,documentation:`OpenVPN outbound из Mihomo 1.19.25. Требует ca/tls-crypt и cert+key либо username/password.`,insertText:`name: "openvpn"
type: openvpn
server: vpn.example.com
port: 1194
proto: udp
cipher: AES-128-GCM
auth: SHA256
username: "user"
password: "pass"
ca: |
  -----BEGIN CERTIFICATE-----
  ...
  -----END CERTIFICATE-----
tls-crypt: |
  -----BEGIN OpenVPN Static key V1-----
  ...
  -----END OpenVPN Static key V1-----
udp: true`,monacoSnippet:`name: "\${1:openvpn}"
type: openvpn
server: \${2:vpn.example.com}
port: \${3:1194}
proto: \${4|udp,tcp|}
cipher: \${5|AES-128-GCM,AES-256-GCM|}
auth: SHA256
username: "\${6:user}"
password: "\${7:pass}"
ca: |
  \${8:-----BEGIN CERTIFICATE-----}
  \${9:...}
  \${10:-----END CERTIFICATE-----}
tls-crypt: |
  \${11:-----BEGIN OpenVPN Static key V1-----}
  \${12:...}
  \${13:-----END OpenVPN Static key V1-----}
udp: true$0`},{id:`mihomo-proxy-tailscale`,label:`proxy: tailscale`,detail:`Mihomo · proxies[]`,documentation:`Tailscale outbound из Mihomo 1.19.25. Не требует server/port; для выхода в интернет нужен exit-node или subnet routes.`,insertText:`name: "tailscale"
type: tailscale
hostname: xkeen
state-dir: ./tailscale
udp: true
accept-routes: true
exit-node: auto:any`,monacoSnippet:`name: "\${1:tailscale}"
type: tailscale
hostname: \${2:xkeen}
state-dir: \${3:./tailscale}
udp: true
accept-routes: \${4|true,false|}
exit-node: \${5:auto:any}$0`}],se=[{id:`mihomo-group-select`,label:`proxy-group: select`,detail:`Mihomo · proxy-groups[]`,documentation:`Ручной выбор — пользователь выбирает активный прокси в UI.`,insertText:`name: "select-manual"
type: select
proxies:
  - "vless-proxy"
  - "trojan-proxy"
  - "DIRECT"`,monacoSnippet:`name: "\${1:select-manual}"
type: select
proxies:
  - "\${2:vless-proxy}"
  - "\${3:trojan-proxy}"
  - "\${4:DIRECT}"$0`},{id:`mihomo-group-url-test`,label:`proxy-group: url-test`,detail:`Mihomo · proxy-groups[]`,documentation:`Автовыбор самого быстрого прокси по ping URL. На Keenetic interval >= 300 — 300+ прокси нагружают роутер.`,insertText:`name: "auto"
type: url-test
proxies:
  - "vless-proxy"
  - "trojan-proxy"
url: "http://www.gstatic.com/generate_204"
interval: 300
tolerance: 50`,monacoSnippet:`name: "\${1:auto}"
type: url-test
proxies:
  - "\${2:vless-proxy}"
  - "\${3:trojan-proxy}"
url: "\${4:http://www.gstatic.com/generate_204}"
interval: \${5:300}
tolerance: \${6:50}$0`},{id:`mihomo-group-fallback`,label:`proxy-group: fallback`,detail:`Mihomo · proxy-groups[]`,documentation:`Переключается на следующий прокси, если предыдущий недоступен.`,insertText:`name: "fallback"
type: fallback
proxies:
  - "vless-proxy"
  - "trojan-proxy"
  - "ss-proxy"
url: "http://www.gstatic.com/generate_204"
interval: 300`,monacoSnippet:`name: "\${1:fallback}"
type: fallback
proxies:
  - "\${2:vless-proxy}"
  - "\${3:trojan-proxy}"
  - "\${4:ss-proxy}"
url: "\${5:http://www.gstatic.com/generate_204}"
interval: \${6:300}$0`},{id:`mihomo-group-load-balance`,label:`proxy-group: load-balance`,detail:`Mihomo · proxy-groups[]`,documentation:`Распределяет соединения по прокси. Стратегия round-robin или consistent-hashing.`,insertText:`name: "load-balance"
type: load-balance
proxies:
  - "vless-proxy"
  - "trojan-proxy"
url: "http://www.gstatic.com/generate_204"
interval: 300
strategy: round-robin`,monacoSnippet:`name: "\${1:load-balance}"
type: load-balance
proxies:
  - "\${2:vless-proxy}"
  - "\${3:trojan-proxy}"
url: "\${4:http://www.gstatic.com/generate_204}"
interval: \${5:300}
strategy: \${6|round-robin,consistent-hashing,sticky-sessions|}$0`}],ce=[{id:`mihomo-proxy-provider-http`,label:`proxy-provider: http (subscription)`,detail:`Mihomo · proxy-providers`,documentation:`Provider подписки. health-check.interval = 300+ рекомендуется, чтобы не перегружать роутер.`,insertText:`subscription:
  type: http
  url: "https://example.com/subscription"
  interval: 86400
  path: ./providers/subscription.yaml
  health-check:
    enable: true
    interval: 300
    url: "http://www.gstatic.com/generate_204"`,monacoSnippet:`\${1:subscription}:
  type: http
  url: "\${2:https://example.com/subscription}"
  interval: \${3:86400}
  path: \${4:./providers/subscription.yaml}
  health-check:
    enable: true
    interval: \${5:300}
    url: "\${6:http://www.gstatic.com/generate_204}"$0`}],le=[{id:`mihomo-rule-provider-domain`,label:`rule-provider: domain list`,detail:`Mihomo · rule-providers`,documentation:`Provider списка доменов (rule type: domain).`,insertText:`ads-list:
  type: http
  behavior: domain
  url: "https://example.com/ads.yaml"
  interval: 86400
  path: ./rules/ads-list.yaml
  format: yaml`,monacoSnippet:`\${1:ads-list}:
  type: http
  behavior: \${2|domain,ipcidr,classical|}
  url: "\${3:https://example.com/ads.yaml}"
  interval: \${4:86400}
  path: \${5:./rules/ads-list.yaml}
  format: \${6|yaml,text,mrs|}$0`}],ue=[{id:`mihomo-rule-ruleset`,label:`rule: RULE-SET -> group`,detail:`Mihomo · rules[]`,documentation:`Применяет rule-provider через RULE-SET и направляет совпадения в proxy-group или встроенный target.`,insertText:`RULE-SET,custom-list,auto`,monacoSnippet:"RULE-SET,${1:custom-list},${2:auto}$0"},{id:`mihomo-rule-domain-suffix`,label:`rule: DOMAIN-SUFFIX -> group`,detail:`Mihomo · rules[]`,documentation:`Маршрутизация по доменному суффиксу. Подходит для простых targeted-rules без provider.`,insertText:`DOMAIN-SUFFIX,example.com,auto`,monacoSnippet:"DOMAIN-SUFFIX,${1:example.com},${2:auto}$0"},{id:`mihomo-rule-geoip-direct`,label:`rule: GEOIP -> DIRECT`,detail:`Mihomo · rules[]`,documentation:`Направляет трафик выбранной страны напрямую. Типовой baseline для локального/регионального трафика.`,insertText:`GEOIP,RU,DIRECT`,monacoSnippet:"GEOIP,${1:RU},${2:DIRECT}$0"}],de=[{id:`mihomo-bundle-rule-provider-ruleset`,label:`rule-provider + RULE-SET`,detail:`Mihomo · rule-providers + rules`,documentation:`Готовый scaffold для provider и соответствующего RULE-SET правила. Хороший старт для ads/custom lists.`,insertText:`rule-providers:
  custom-list:
    type: http
    behavior: domain
    url: "https://example.com/rules/custom-list.yaml"
    interval: 86400
    path: ./rules/custom-list.yaml
    format: yaml
rules:
  - RULE-SET,custom-list,auto`,monacoSnippet:`rule-providers:
  \${1:custom-list}:
    type: http
    behavior: \${2|domain,ipcidr,classical|}
    url: "\${3:https://example.com/rules/custom-list.yaml}"
    interval: \${4:86400}
    path: \${5:./rules/custom-list.yaml}
    format: \${6|yaml,text,mrs|}
rules:
  - RULE-SET,\${1:custom-list},\${7:auto}$0`},{id:`mihomo-dns-block`,label:`dns block (Keenetic — обычно не нужен)`,detail:`Mihomo · dns`,documentation:`DNS-блок Mihomo. Настраивает nameserver, fake-ip и fallback. Обычно нужен только если активно используется TUN/transparent-режим.`,warning:ee,insertText:`dns:
  enable: true
  ipv6: false
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  fake-ip-filter:
    - "*.lan"
    - "localhost.ptlogin2.qq.com"
  nameserver:
    - https://1.1.1.1/dns-query
    - https://dns.google/dns-query
  fallback:
    - tls://8.8.4.4:853
  fallback-filter:
    geoip: true
    geoip-code: RU`,monacoSnippet:`dns:
  enable: true
  ipv6: \${1|false,true|}
  enhanced-mode: \${2|fake-ip,redir-host|}
  fake-ip-range: \${3:198.18.0.1/16}
  fake-ip-filter:
    - "*.lan"
    - "localhost.ptlogin2.qq.com"
  nameserver:
    - \${4:https://1.1.1.1/dns-query}
    - \${5:https://dns.google/dns-query}
  fallback:
    - \${6:tls://8.8.4.4:853}
  fallback-filter:
    geoip: true
    geoip-code: \${7:RU}$0`},{id:`mihomo-tun-block`,label:`tun block (Keenetic — обычно не нужен)`,detail:`Mihomo · tun`,documentation:`TUN-блок Mihomo. Включает виртуальный сетевой интерфейс для transparent-проксирования.`,warning:g,insertText:`tun:
  enable: true
  stack: system
  auto-route: true
  auto-detect-interface: true
  dns-hijack:
    - any:53
    - tcp://any:53
  mtu: 9000
  strict-route: true`,monacoSnippet:`tun:
  enable: \${1|true,false|}
  stack: \${2|system,gvisor,mixed|}
  auto-route: true
  auto-detect-interface: true
  dns-hijack:
    - any:53
    - tcp://any:53
  mtu: \${3:9000}
  strict-route: \${4|true,false|}$0`},{id:`mihomo-sniffer-block`,label:`sniffer block`,detail:`Mihomo · sniffer`,documentation:`Sniffer — восстанавливает host/SNI из пакетов для правильного матчинга в rules. На Keenetic безопасен и рекомендуется.`,insertText:`sniffer:
  enable: true
  sniff:
    HTTP:
    TLS:`,monacoSnippet:`sniffer:
  enable: \${1|true,false|}
  sniff:
    HTTP:
    TLS:$0`}];function v(e){if(e==null)return``;let t=String(e);return t?(t.charAt(0)!==`/`&&(t=`/${t}`),t):``}function y(e){return Array.isArray(e)?e.map(e=>String(e??``)):[]}function fe(e){return e==null?!1:/^\d+$/.test(String(e))}function pe(e){let t=String(e||``).toLowerCase();return t===`array-item`||t===`key`||t===`value`?t:``}function me(e){let t=v(e);return t?!!(/^\/rules$/.test(t)||/^\/routing\/rules$/.test(t)):!1}function he(e){let t=v(e);return t?!!(/^\/balancers$/.test(t)||/^\/routing\/balancers$/.test(t)):!1}function ge(e){let t=v(e);return t?/^\/outbounds$/.test(t):!1}function _e(e){let t=v(e);return t?/^\/inbounds$/.test(t):!1}function ve(e){let t=v(e);return t?/\/streamSettings$/.test(t):!1}function ye(e){let t=v(e);return t===``||t===`/`}function be(e){return y(e).length===0}function xe(e,t,n,r={}){let i=y(e),a=pe(n),o=!!r.allowValue;return!i.length||i[0]!==t?!1:i.length===1?!a||a===`key`:i.length!==2||!fe(i[1])?!1:!a||a===`array-item`||a===`key`?!0:o&&a===`value`}function Se(e,t,n){let r=y(e),i=pe(n);return!r.length||r[0]!==t?!1:r.length===1&&(!i||i===`key`)}function Ce(e,t){return xe(e,`proxies`,t)}function we(e,t){return xe(e,`proxy-groups`,t)}function Te(e,t){return xe(e,`rules`,t,{allowValue:!0})}function Ee(e,t){return Se(e,`proxy-providers`,t)}function De(e,t){return Se(e,`rule-providers`,t)}function Oe(e){let t=String(e||``).toLowerCase();return t?t.includes(`routing`)?`xray-routing`:t.includes(`outbound`)?`xray-outbounds`:t.includes(`inbound`)?`xray-inbounds`:t.includes(`config`)||t===`xray`?`xray-config`:t:``}function ke(e){let t=e&&typeof e==`object`?e:{},n=Oe(t.schemaKind),r=v(t.pointer),i=[];return(n===`xray-routing`||n===`xray-config`)&&(me(r)&&i.push(...te),he(r)&&i.push(...ne)),n===`xray-outbounds`&&((ge(r)||r===``||r===`/`)&&i.push(...re),ve(r)&&i.push(..._)),n===`xray-inbounds`&&((_e(r)||r===``||r===`/`)&&i.push(...ie),ve(r)&&i.push(..._)),n===`xray-config`&&(ge(r)&&i.push(...re),_e(r)&&i.push(...ie),ve(r)&&i.push(..._),ye(r)&&i.push(...ae)),i.map(Me)}function Ae(e){let t=e&&typeof e==`object`?e:{},n=y(t.path),r=pe(t.kind),i=[];return be(n)&&i.push(...de),Ce(n,r)&&i.push(...oe),we(n,r)&&i.push(...se),Ee(n,r)&&i.push(...ce),De(n,r)&&i.push(...le),Te(n,r)&&i.push(...ue),i.map(Me)}function b(e){let t=Oe(e);return function(e){let n=e&&typeof e==`object`?e:{};return ke({schemaKind:n.schemaKind||t,pointer:n.pointer||``})}}function je(){return function(e){let t=e&&typeof e==`object`?e:{};return Ae({path:t.path||[],kind:t.kind||``})}}function Me(e){return!e||typeof e!=`object`?e:{id:String(e.id||``),label:String(e.label||``),kind:`snippet`,detail:String(e.detail||``),documentation:String(e.documentation||``),warning:e.warning?String(e.warning):null,insertText:String(e.insertText||``),monacoSnippet:String(e.monacoSnippet||e.insertText||``)}}function Ne(e){if(!e||typeof e!=`object`)return``;let t=[];return e.documentation&&t.push(String(e.documentation)),e.warning&&t.push(`⚠ ${String(e.warning)}`),t.join(`

`)}function Pe(e,t={}){let n=Array.isArray(e)?e:[],r=t&&t.mode===`monaco`?`monaco`:`cm6`;return n.filter(e=>e&&typeof e==`object`&&e.label&&(e.insertText||e.monacoSnippet)).map(e=>({id:e.id,label:e.label,type:`snippet`,detail:e.detail||``,insertText:r===`monaco`&&e.monacoSnippet||e.insertText,useSnippetSyntax:r===`monaco`,documentation:Ne(e),warning:e.warning||null}))}Object.freeze({getXraySnippets:ke,getMihomoSnippets:Ae,createXraySnippetProvider:b,createMihomoSnippetProvider:je,renderSnippetDocumentation:Ne,snippetsToCompletionOptions:Pe});var x=Object.freeze({insertSpaces:!0,tabSize:2,eol:`
`}),S=`http://www.gstatic.com/generate_204`,C=86400;function w(e){return e==null?``:String(e)}function T(e){return w(e).trim()}function Fe(e){let t=T(e);return t?/^\d{1,3}(?:\.\d{1,3}){3}$/.test(t)?!0:/^[0-9a-f:.]+$/i.test(t)&&t.includes(`:`):!1}function E(e){if(!e||typeof e!=`object`||Array.isArray(e))return!1;let t=Object.getPrototypeOf(e);return t===Object.prototype||t===null}function D(e){if(typeof e!=`object`||!e)return e;if(Array.isArray(e))return e.map(e=>D(e));if(!E(e))return e;let t={};return Object.keys(e).forEach(n=>{t[n]=D(e[n])}),t}function O(e){let t=T(e);if(!t)return[];let n=[],r=``;for(let e=0;e<t.length;e+=1){let i=t.charAt(e);if(i===`.`){r&&n.push(r),r=``;continue}if(i===`[`){r&&n.push(r),r=``;let i=t.indexOf(`]`,e+1);i<0&&(i=t.length);let a=t.slice(e+1,i);n.push(/^\d+$/.test(a)?Number(a):a),e=i;continue}r+=i}return r&&n.push(r),n}function k(e){let t=T(e);return!t||t===`/`?[]:t.split(`/`).slice(1).map(e=>{let t=e.replace(/~1/g,`/`).replace(/~0/g,`~`);return/^\d+$/.test(t)?Number(t):t})}function A(e){let t=Array.isArray(e)?e:[];return t.length?t.reduce((e,t)=>`${e}/${String(t??``).replace(/~/g,`~0`).replace(/\//g,`~1`)}`,``):``}function j(e,t){let n=Array.isArray(t)?t:[],r=e;for(let e=0;e<n.length;e+=1){let t=n[e];if(r==null)return;if(typeof t==`number`){if(!Array.isArray(r)||t<0||t>=r.length)return;r=r[t];continue}if(!Object.prototype.hasOwnProperty.call(Object(r),t))return;r=r[t]}return r}function Ie(e,t){return j(e,k(t))}function M(e){return Array.from(new Set((Array.isArray(e)?e:[]).map(T).filter(Boolean)))}function Le(e,t){let n=o(e,t)||e;if(!n||typeof n!=`object`)return null;let r=[`oneOf`,`anyOf`,`allOf`];for(let e=0;e<r.length;e+=1){let i=r[e];if(!(!Array.isArray(n[i])||!n[i].length))for(let e=0;e<n[i].length;e+=1){let r=Le(n[i][e],t);if(r)return r}}return n}function Re(e,t){let n=Le(e,t);return!n||!n.type?[]:Array.isArray(n.type)?n.type.map(e=>T(e)).filter(Boolean):[T(n.type)].filter(Boolean)}function ze(e,t){let n=Le(e,t);if(!n||typeof n!=`object`)return``;if(Object.prototype.hasOwnProperty.call(n,`default`))return D(n.default);if(Object.prototype.hasOwnProperty.call(n,`const`))return D(n.const);if(Array.isArray(n.enum)&&n.enum.length){let e=new Set((Array.isArray(n.deprecatedValues)?n.deprecatedValues:[]).map(e=>JSON.stringify(e))),t=n.enum.find(t=>!e.has(JSON.stringify(t)));return D(t===void 0?n.enum[0]:t)}let r=Re(n,t);return r.includes(`object`)||n.properties||n.additionalProperties||n.patternProperties?{}:r.includes(`array`)||n.items?[]:r.includes(`boolean`)?!1:r.includes(`integer`)||r.includes(`number`)?0:r.includes(`null`)?null:``}function Be(e,t,n){let r=o(e,n)||e;if(!r||typeof r!=`object`)return null;if(r.properties&&Object.prototype.hasOwnProperty.call(r.properties,t))return o(r.properties[t],n)||r.properties[t];if(r.patternProperties){let e=Object.keys(r.patternProperties);for(let i=0;i<e.length;i+=1){let a=e[i];try{if(new RegExp(a,`u`).test(t))return o(r.patternProperties[a],n)||r.patternProperties[a]}catch{}}}if(r.additionalProperties&&typeof r.additionalProperties==`object`)return o(r.additionalProperties,n)||r.additionalProperties;let i=[`allOf`,`anyOf`,`oneOf`];for(let e=0;e<i.length;e+=1){let a=i[e];if(Array.isArray(r[a]))for(let e=0;e<r[a].length;e+=1){let i=Be(r[a][e],t,n);if(i)return i}}return null}function Ve(e){return(Array.isArray(e)?e:[]).map(e=>{let t=Math.max(0,Number(e&&(e.from==null?e.offset:e.from)||0));return{from:t,to:Math.max(t,Number(e&&(e.to==null?e.offset==null?t:Number(e.offset)+Number(e.length||0):e.to)||t)),insert:w(e&&(e.insert==null?e.content:e.insert))}}).sort((e,t)=>e.from===t.from?e.to-t.to:e.from-t.from)}function He(e){return Ve((Array.isArray(e)?e:[]).map(e=>({offset:Number(e&&e.offset||0),length:Number(e&&e.length||0),content:w(e&&e.content)})))}function Ue(e,t){let n=w(e),r=Ve(t);if(!r.length)return n;let i=n;for(let e=r.length-1;e>=0;--e){let t=r[e];i=i.slice(0,t.from)+t.insert+i.slice(t.to)}return i}function We(e,t){return!t||typeof t!=`object`?w(e):typeof t.text==`string`?t.text:Array.isArray(t.edits)&&t.edits.length?Ue(e,t.edits):w(e)}function N(e,t){let n=Ve(t);if(!n.length)return null;let r=Number.isFinite(e&&e.rangeFrom)?Math.max(0,Number(e.rangeFrom)):n[0].from,i=n[n.length-1],a=Number.isFinite(e&&e.rangeTo)?Math.max(r,Number(e.rangeTo)):Math.max(i.to,r+1);return{id:T(e&&e.id)||`fix-${Math.random().toString(36).slice(2,9)}`,title:T(e&&e.title)||`Исправить`,label:T(e&&e.label)||T(e&&e.title)||`Исправить`,code:T(e&&e.code),isPreferred:!!(e&&e.isPreferred),priority:Number.isFinite(e&&e.priority)?Number(e.priority):0,rangeFrom:r,rangeTo:a,family:T(e&&e.family),edits:n}}function Ge(e){let t=new Set;return(Array.isArray(e)?e:[]).filter(e=>{if(!e||!e.id||!e.title)return!1;let n=`${e.id}\u0000${e.title}\u0000${e.rangeFrom}\u0000${e.rangeTo}`;return t.has(n)?!1:(t.add(n),!0)})}function Ke(e,t){let n=Ge(e).sort((e,t)=>!!e.isPreferred==!!t.isPreferred?(Number(e.priority)||0)===(Number(t.priority)||0)?e.rangeFrom===t.rangeFrom?e.title.localeCompare(t.title):e.rangeFrom-t.rangeFrom:(Number(t.priority)||0)-(Number(e.priority)||0):e.isPreferred?-1:1),r=Number.isFinite(t&&t.offset)?Math.max(0,Number(t.offset)):NaN,i=Number.isFinite(r)?(()=>{let e=n.filter(e=>r>=e.rangeFrom&&r<=e.rangeTo);return e.length?e:n})():n,a=Math.max(0,Number(t&&t.limit||0));return a>0?i.slice(0,a):i}function qe(e,t){let n=w(e),r=w(t);if(!n)return r.length;if(!r)return n.length;let i=Array(r.length+1),a=Array(r.length+1);for(let e=0;e<=r.length;e+=1)i[e]=e;for(let e=0;e<n.length;e+=1){a[0]=e+1;for(let t=0;t<r.length;t+=1){let o=n.charAt(e)===r.charAt(t)?0:1;a[t+1]=Math.min(a[t]+1,i[t+1]+1,i[t]+o)}for(let e=0;e<=r.length;e+=1)i[e]=a[e]}return i[r.length]}function P(e,t,n=[]){let r=T(e),i=M(t);if(!i.length)return``;let a=M(n).filter(e=>i.includes(e));if(!r)return a[0]||i[0];let o=``,s=1/0;return a.concat(i.filter(e=>!a.includes(e))).forEach((e,t)=>{let n=qe(r.toLowerCase(),e.toLowerCase())+t/1e3;n<s&&(s=n,o=e)}),o}function Je(e){return P(``,e,[`direct`,`proxy`,`block`])}function F(e,t){let n=u(c(w(e)),T(t));if(!n)return{from:0,to:1};let r=Number.isFinite(n.valueFrom)?Number(n.valueFrom):Number(n.keyFrom||0),i=Number.isFinite(n.valueTo)?Number(n.valueTo):Number(n.keyTo||r+1);return{from:Math.max(0,r),to:Math.max(Math.max(0,r)+1,i)}}function I(e,t,n,r){let i=[];try{i=f(w(e),Array.isArray(t)?t:[],n,{formattingOptions:x})}catch{i=[]}return N(r,He(i))}function Ye(e){let t=T(e).toLowerCase();return t===`ws`?`wsSettings`:t===`grpc`?`grpcSettings`:t===`httpupgrade`?`httpupgradeSettings`:``}function Xe(e){let t=T(e).toLowerCase();return t===`ws`||t===`httpupgrade`?{path:`/`}:t===`grpc`?{serviceName:`grpc`}:{}}function Ze(e){let t=E(e&&e.routing)?e.routing:e;return M((Array.isArray(t&&t.balancers)?t.balancers:[]).map(e=>e&&e.tag))}function Qe(e){if(!E(e)||!E(e.settings))return``;let t=e.settings;return Array.isArray(t.vnext)&&t.vnext.length?T(t.vnext[0]&&t.vnext[0].address):Array.isArray(t.servers)&&t.servers.length?T(t.servers[0]&&t.servers[0].address):T(t.address)}function $e(e){let t=M(e);return{subjectSelector:t.length?t:[`proxy-`],probeUrl:S,probeInterval:`60s`}}function et(e){let t=M(e);return{subjectSelector:t.length?t:[`proxy-`],pingConfig:{destination:`1.1.1.1:80`,connectivity:S,interval:`30s`,sampling:5,timeout:`5s`}}}function tt(e,t,n){let r=[],i=E(t&&t.routing)?t.routing:t,a=i===t?[]:[`routing`],o=Array.isArray(i&&i.balancers)?i.balancers:[],s=n&&typeof n==`object`?n:{},c=!!(E(t&&t.observatory)||E(i&&i.observatory)||E(s.externalObservatory)),l=!!(E(t&&t.burstObservatory)||E(i&&i.burstObservatory)||E(s.externalBurstObservatory));return o.forEach((t,n)=>{if(!E(t))return;let i=T(t&&t.strategy&&t.strategy.type)||`random`,o=a.concat(`balancers`,n),s=F(e,A(o.concat(`strategy`,`type`))),u=M(Array.isArray(t.selector)?t.selector:[]);if(i===`leastPing`&&!c){let t=I(e,[`observatory`],$e(u),{id:`xray-observatory-add-${o.join(`.`)}`,title:"Добавить блок `observatory`",code:`balancer-observatory-missing`,isPreferred:!0,priority:90,rangeFrom:s.from,rangeTo:s.to,family:`semantic`});t&&r.push(t)}if(i===`leastLoad`&&!l){let t=I(e,[`burstObservatory`],et(u),{id:`xray-burst-observatory-add-${o.join(`.`)}`,title:"Добавить блок `burstObservatory`",code:`balancer-burst-observatory-missing`,isPreferred:!0,priority:90,rangeFrom:s.from,rangeTo:s.to,family:`semantic`});t&&r.push(t)}}),r}function L(e,t,n){if(Array.isArray(e)){n(t,e),e.forEach((e,r)=>L(e,t.concat(r),n));return}if(E(e)){n(t,e),Object.keys(e).forEach(r=>L(e[r],t.concat(r),n));return}n(t,e)}function nt(e,t,n){if(!n||t==null)return[];let r=[],i=[];try{i=d(t,n,n,``)}catch{i=[]}return i.forEach(i=>{let a=T(i&&i.pointer),c=T(i&&i.message);if(!a||!c)return;let l=F(e,a),u=k(a),d=Ie(t,a),f=c.match(/`([^`]+)`/);if(c.includes(`отсутствует`)&&f&&u.length){let t=T(f[1]),i=u.slice(0,-1),a=ze(Be(s(n,n,A(i)),t,n),n),o=I(e,i.concat(t),a,{id:`json-required-${i.join(`.`)}-${t}`,title:`Добавить поле \`${t}\``,code:`schema-required-missing`,isPreferred:!0,rangeFrom:l.from,rangeTo:l.to,family:`schema`});o&&r.push(o);return}let p=s(n,n,a);if(Re(p,n).includes(`array`)&&!Array.isArray(d)&&d!==void 0){let t=I(e,u,[D(d)],{id:`json-array-wrap-${u.join(`.`)}`,title:`Обернуть значение в массив`,code:`schema-wrap-array`,isPreferred:!0,rangeFrom:l.from,rangeTo:l.to,family:`schema`});t&&r.push(t);return}let m=o(p,n)||p,h=Array.isArray(m&&m.deprecatedValues)?m.deprecatedValues:[];if(h.length&&h.some(e=>e===d)){let t=(()=>{let e=Array.isArray(m&&m.enum)?m.enum:[];return d===`grpc`&&e.includes(`xhttp`)?`xhttp`:e.find(e=>!h.includes(e)&&e!==d)})();if(t!=null&&t!==d){let n=I(e,u,t,{id:`json-deprecated-${u.join(`.`)}`,title:`Заменить \`${d}\` на \`${t}\``,code:`schema-deprecated-value`,isPreferred:!0,rangeFrom:l.from,rangeTo:l.to,family:`schema`});n&&r.push(n)}}}),L(t,[],(t,n)=>{if(!E(n)||!E(n.streamSettings))return;let i=T(n.streamSettings.network),a=Ye(i);if(!a||Object.prototype.hasOwnProperty.call(n.streamSettings,a))return;let o=F(e,A(t.concat(`streamSettings`,`network`))),s=I(e,t.concat(`streamSettings`,a),Xe(i),{id:`json-transport-${t.join(`.`)}-${a}`,title:`Добавить блок \`${a}\``,code:`transport-block-missing`,rangeFrom:o.from,rangeTo:o.to,family:`transport`});s&&r.push(s)}),r}function rt(e,t,n){let i=[],a=r(t,n||{}),o=M(n&&n.knownOutboundTags||[]),s=M(n&&n.knownInboundTags||[]),c=Ze(t);return a.forEach(n=>{let r=T(n&&n.code),a=T(n&&n.pointer),l=k(a),u=F(e,a||`/`);if(r===`rule-missing-target`&&l.length){let t=Je(o);if(!t)return;let n=I(e,l.concat(`outboundTag`),t,{id:`xray-rule-target-${l.join(`.`)}`,title:`Добавить \`outboundTag: ${t}\``,code:r,isPreferred:!0,priority:95,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});n&&i.push(n);return}if((r===`outbound-tag-missing`||r===`balancer-tag-missing`||r===`inbound-tag-missing`)&&l.length){let n=T(j(t,l)),a=P(n,r===`outbound-tag-missing`?o:r===`balancer-tag-missing`?c:s,r===`outbound-tag-missing`?[`direct`,`proxy`,`block`]:[]);if(!a||a===n)return;let d=I(e,l,a,{id:`xray-tag-replace-${r}-${l.join(`.`)}`,title:`Заменить на \`${a}\``,code:r,isPreferred:!0,priority:95,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});d&&i.push(d);return}if(r===`balancer-selector-empty`&&l.length){let t=Je(o);if(!t)return;let n=I(e,l.concat(`selector`),[t],{id:`xray-balancer-selector-${l.join(`.`)}`,title:`Добавить selector с \`${t}\``,code:r,isPreferred:!0,priority:90,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});n&&i.push(n);return}if(r===`balancer-observatory-missing`&&l.length>=2){let n=l.slice(0,-2),a=j(t,n),o=I(e,[`observatory`],$e(M(Array.isArray(a&&a.selector)?a.selector:[])),{id:`xray-observatory-add-${n.join(`.`)}`,title:"Добавить блок `observatory`",code:r,isPreferred:!0,priority:90,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});o&&i.push(o);return}if(r===`balancer-burst-observatory-missing`&&l.length>=2){let n=l.slice(0,-2),a=j(t,n),o=I(e,[`burstObservatory`],et(M(Array.isArray(a&&a.selector)?a.selector:[])),{id:`xray-burst-observatory-add-${n.join(`.`)}`,title:"Добавить блок `burstObservatory`",code:r,isPreferred:!0,priority:90,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});o&&i.push(o);return}if(r===`observatory-duplicates-external`){let t=I(e,[`observatory`],void 0,{id:`xray-observatory-remove-duplicate-external`,title:"Удалить локальный дубль `observatory`",code:r,isPreferred:!0,priority:100,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});t&&i.push(t);return}if(r===`outbound-tls-server-name-suggested`&&l.length>=2){let n=Qe(j(t,l.slice(0,-2)));if(!n||Fe(n))return;let a=I(e,l.concat(`serverName`),n,{id:`xray-tls-servername-${l.join(`.`)}`,title:`Добавить \`serverName: ${n}\``,code:r,isPreferred:!0,priority:80,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});a&&i.push(a);return}if(r===`outbound-reality-server-name-missing`&&l.length>=2){let n=Qe(j(t,l.slice(0,-2)));if(!n||Fe(n))return;let a=I(e,l.concat(`serverName`),n,{id:`xray-reality-servername-${l.join(`.`)}`,title:`Добавить \`serverName: ${n}\``,code:r,isPreferred:!0,priority:80,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});a&&i.push(a);return}if(r===`inbound-reality-shortids-missing`&&l.length){let t=I(e,l.concat(`shortIds`),[``],{id:`xray-reality-shortids-${l.join(`.`)}`,title:'Добавить `shortIds: [""]`',code:r,isPreferred:!0,priority:85,rangeFrom:u.from,rangeTo:u.to,family:`semantic`});t&&i.push(t);return}if(r===`private-ip-rule-not-first`&&l.length>=3){let n=l[l.length-1];if(typeof n!=`number`||n<=0)return;let a=l.slice(0,-1),o=j(t,a);if(!Array.isArray(o))return;let s=o[n];if(!E(s))return;let c=[];try{let t=f(w(e),a.concat(0),D(s),{formattingOptions:x,isArrayInsertion:!0}),r=f(w(e),a.concat(n),void 0,{formattingOptions:x});c=He([].concat(t,r))}catch{c=[]}if(!c.length)return;let d=N({id:`xray-private-ip-move-${l.join(`.`)}`,title:`Переместить LAN-правило в начало routing.rules`,code:r,isPreferred:!0,priority:100,rangeFrom:u.from,rangeTo:u.to,family:`semantic`},c);d&&i.push(d)}}),i.push(...tt(e,t,n)),i}function it(e,t){let n=e&&typeof e.getSemanticOptions==`function`?e.getSemanticOptions:null;if(n)try{return n(t)||{}}catch{}return e&&typeof e.semanticOptions==`object`?e.semanticOptions:{}}function at(e){let t=w(e);return t.length-t.replace(/^\s+/,``).length}function R(e,t){let n=` `.repeat(Math.max(0,Number(t||0)));return w(e).split(`
`).map(e=>e&&`${n}${e}`).join(`
`)}function ot(e){return typeof e==`string`?e===``?`""`:/^[A-Za-z0-9_./@:-]+$/.test(e)?e:JSON.stringify(e):typeof e==`number`||typeof e==`boolean`?String(e):e===null?`null`:w(e)}function z(e,t,r){let i=Array.isArray(t)?n(t):T(t),a=Array.isArray(e&&e.tokens)?e.tokens:[],o=null;for(let e=0;e<a.length;e+=1){let t=a[e];!t||n(t.path)!==i||r&&T(t.kind)!==T(r)||(!o||t.to-t.from<o.to-o.from)&&(o=t)}return o}function st(e,t,r){let i=z(e,t,`value`);if(!i)return null;if(Array.isArray(r)||E(r)){let a=Array.isArray(t)?t.slice():O(t),o=e&&e.map?e.map.get(n(a)):null,s=Math.max(0,Number(o&&o.column||1)+1),c=p(D(r),{noRefs:!0,lineWidth:-1}).trimEnd();return{from:i.from,to:i.to,insert:`\n${R(c,s)}`}}return{from:i.from,to:i.to,insert:ot(r)}}function ct(e,t){let r=Array.isArray(t)?t:O(t);if(!r.length)return{offset:e&&typeof e.normalized==`string`?e.normalized.length:0,indent:0};let i=e&&e.map?e.map.get(n(r)):null;if(!i)return{offset:e&&typeof e.normalized==`string`?e.normalized.length:0,indent:0};let a=Math.max(0,Number(i.column||1)-1),o=Math.max(0,Number(i.line||1)),s=Array.isArray(e&&e.lines)?e.lines:[],c=Array.isArray(e&&e.starts)?e.starts:[];for(;o<s.length;){let e=s[o];if(!w(e).trim()){o+=1;continue}if(at(e)<=a)break;o+=1}return{offset:o<c.length?c[o]:e&&typeof e.normalized==`string`?e.normalized.length:0,indent:a+2}}function lt(e,t,n){return R(p({[e]:D(t)},{noRefs:!0,lineWidth:-1}).trimEnd(),n)}function ut(e,t){return R(p(Array.isArray(e)?D(e):[],{noRefs:!0,lineWidth:-1}).trimEnd(),t)}function B(e,t,r,i,a,o){let s=w(e),c=Array.isArray(r)?r:O(r);if(!c.length){let e=lt(i,a,0),t=s.trim()?s.endsWith(`
`)?`
`:`

`:``;return N(o,[{from:s.length,to:s.length,insert:`${t}${e}\n`}])}if(c.length===1&&!(t&&t.map&&t.map.has(n(c)))){let e=p({[c[0]]:{[i]:D(a)}},{noRefs:!0,lineWidth:-1}).trimEnd(),t=s.trim()?s.endsWith(`
`)?`
`:`

`:``;return N(o,[{from:s.length,to:s.length,insert:`${t}${e}\n`}])}let l=ct(t,c),u=`${lt(i,a,l.indent)}\n`,d=l.offset>0&&s.charAt(l.offset-1)!==`
`?`
`:``;return N(o,[{from:l.offset,to:l.offset,insert:`${d}${u}`}])}function dt(e,t,r,i,a){let o=w(e),s=[T(r)];if(!(t&&t.map&&t.map.has(n(s)))){let e=p({[r]:[D(i)]},{noRefs:!0,lineWidth:-1}).trimEnd(),t=o.trim()?o.endsWith(`
`)?`
`:`

`:``;return N(a,[{from:o.length,to:o.length,insert:`${t}${e}\n`}])}let c=ct(t,s),l=`${ut([i],c.indent)}\n`,u=c.offset>0&&o.charAt(c.offset-1)!==`
`?`
`:``;return N(a,[{from:c.offset,to:c.offset,insert:`${u}${l}`}])}function V(e,t,n,r,i){let a=st(t,n,r);return a?N(i,[a]):null}function ft(e,t,n,r,i,a,o){let s=Array.isArray(r)?r.slice():O(r),c=s.concat(i);if(j(n,c)!==void 0){let n=V(e,t,c,a,o);if(n)return n}return B(e,t,s,i,a,o)}function pt(e){let t=T(e);if(!t)return[];let n=[],r=``,i=0,a=``,o=!1;for(let e=0;e<t.length;e+=1){let s=t.charAt(e);if(o){r+=s,o=!1;continue}if(s===`\\`){r+=s,o=!0;continue}if(a){r+=s,s===a&&(a=``);continue}if(s===`"`||s===`'`){r+=s,a=s;continue}if(s===`(`){i+=1,r+=s;continue}if(s===`)`){i=Math.max(0,i-1),r+=s;continue}if(s===`,`&&i===0){n.push(r.trim()),r=``;continue}r+=s}return(r.trim()||!n.length)&&n.push(r.trim()),n.filter(e=>e!==``)}function mt(e){let t={"no-resolve":!0,src:!0,dst:!0};for(let n=e.length-1;n>=1;--n){let r=T(e[n]);if(r&&!t[r.toLowerCase()])return n}return-1}function ht(e){let t=[],n=/\bRULE-SET,([^,\s)]+)/g,r=T(e),i;for(;i=n.exec(r);){let e=T(i[1]);e&&t.push(e)}return M(t)}function gt(e){let t=Array.isArray(e&&e.proxies)?e.proxies:[],n=Array.isArray(e&&e[`proxy-groups`])?e[`proxy-groups`]:[];return M(t.map(e=>e&&e.name).concat(n.map(e=>e&&e.name)))}function _t(e,t){let n=E(e&&e[t])?e[t]:{};return M(Object.keys(n))}function vt(e){let t=T(e).toLowerCase();return t===`ws`?`ws-opts`:t===`grpc`?`grpc-opts`:t===`h2`?`h2-opts`:t===`xhttp`?`xhttp-opts`:``}function yt(e){let t=T(e).toLowerCase();return t===`ws`?{path:`/`}:t===`grpc`?{"grpc-service-name":`grpc`}:t===`h2`?{path:`/`}:t===`xhttp`?{path:`/`,mode:`stream-one`}:{}}function bt(e){let t=T(e)||`ruleset`;return{type:`http`,behavior:`domain`,format:`mrs`,url:`https://example.invalid/${encodeURIComponent(t)}.mrs`,interval:C}}function xt(e){let t=T(e)||`provider`;return{type:`http`,url:`https://example.invalid/${encodeURIComponent(t)}.yaml`,path:`./providers/${t.replace(/[^A-Za-z0-9._-]+/g,`_`)}.yaml`,interval:C,"health-check":{enable:!0,url:S,interval:300}}}function St(e){return{name:T(e)||`AutoGroup`,type:`select`,proxies:[`DIRECT`]}}function Ct(e){if(!E(e))return``;let t=T(e&&e[`ws-opts`]&&e[`ws-opts`].headers&&e[`ws-opts`].headers.Host);if(t)return t;let n=T(e&&e[`xhttp-opts`]&&e[`xhttp-opts`].host);if(n)return n;let r=Array.isArray(e&&e[`h2-opts`]&&e[`h2-opts`].host)?e[`h2-opts`].host.map(T).filter(Boolean):[];if(r.length)return r[0];let i=T(e&&e.server);return i&&!Fe(i)?i:``}function wt(t,n,r){if(!r)return[];let s=[],c=null;try{c=i(t,r,{maxErrors:60})}catch{c=null}let l=a(t);return(c&&Array.isArray(c.diagnostics)?c.diagnostics:[]).forEach(i=>{let a=O(i&&i.path),o=T(i&&i.message),c=o.match(/`([^`]+)`/),u=Math.max(0,Number(i&&i.from||0)),d=Math.max(u+1,Number(i&&i.to||u+1));if(c&&o.toLowerCase().includes(`обяз`)){let i=T(c[1]),o=B(t,l,a,i,ze(Be(e(r,a,n,r),i,r),r),{id:`yaml-required-${a.join(`.`)}-${i}`,title:`Добавить поле \`${i}\``,code:`schema-required-missing`,isPreferred:!0,rangeFrom:u,rangeTo:d,family:`schema`});o&&s.push(o);return}if(a.length){let i=Re(e(r,a,n,r),r),o=j(n,a);if(i.includes(`array`)&&o!==void 0&&!Array.isArray(o)){let e=V(t,l,a,[D(o)],{id:`yaml-array-${a.join(`.`)}`,title:`Обернуть значение в список`,code:`schema-wrap-array`,isPreferred:!0,rangeFrom:u,rangeTo:d,family:`schema`});e&&s.push(e)}}}),(Array.isArray(n&&n.proxies)?n.proxies:[]).forEach((e,n)=>{if(!E(e))return;let r=T(e.network),i=vt(r);if(!i||Object.prototype.hasOwnProperty.call(e,i))return;let a=z(l,[`proxies`,n,`network`],`value`),o=a?a.from:0,c=a?a.to:1,u=B(t,l,[`proxies`,n],i,yt(r),{id:`yaml-transport-${n}-${i}`,title:`Добавить блок \`${i}\``,code:`transport-block-missing`,rangeFrom:o,rangeTo:c,family:`transport`});u&&s.push(u)}),(Array.isArray(l&&l.tokens)?l.tokens.filter(e=>e&&e.kind===`value`).map(e=>e.path):[]).forEach(i=>{let a=e(r,i,n,r),c=j(n,i),u=o(a,r)||a,d=Array.isArray(u&&u.deprecatedValues)?u.deprecatedValues:[];if(!d.length||!d.some(e=>e===c))return;let f=Array.isArray(u&&u.enum)?u.enum:[],p=c===`grpc`&&f.includes(`xhttp`)?`xhttp`:f.find(e=>!d.includes(e)&&e!==c);if(p===void 0||p===c)return;let m=z(l,i,`value`),h=m?m.from:0,ee=m?m.to:1,g=V(t,l,i,p,{id:`yaml-deprecated-${i.join(`.`)}`,title:`Заменить \`${c}\` на \`${p}\``,code:`schema-deprecated-value`,isPreferred:!0,rangeFrom:h,rangeTo:ee,family:`schema`});g&&s.push(g)}),s}function Tt(e,r){let i=[],o=a(e),s=t(r,{}),c=gt(r),l=_t(r,`proxy-providers`),u=_t(r,`rule-providers`);return s.forEach(t=>{let a=T(t&&t.code),s=Array.isArray(t&&t.path)?t.path.slice():[],d=n(s),f=z(o,s,`value`),p=f?f.from:o.map&&o.map.get(d)?o.map.get(d).offset:0,m=f?f.to:Math.max(p+1,p);if((a===`proxy-provider-proxy-missing`||a===`rule-provider-proxy-missing`||a===`proxy-group-target-missing`)&&s.length){let t=T(j(r,s)),n=P(t,c,[`DIRECT`]);if(!n||n===t)return;let l=V(e,o,s,n,{id:`mihomo-replace-${a}-${s.join(`.`)}`,title:`Заменить на \`${n}\``,code:a,isPreferred:!0,priority:95,rangeFrom:p,rangeTo:m,family:`semantic`});l&&i.push(l);return}if(a===`proxy-group-provider-missing`&&s.length){let t=T(j(r,s)),n=P(t,l);if(n&&n!==t){let t=V(e,o,s,n,{id:`mihomo-provider-replace-${s.join(`.`)}`,title:`Заменить provider на \`${n}\``,code:a,isPreferred:!0,priority:90,rangeFrom:p,rangeTo:m,family:`semantic`});t&&i.push(t)}if(t){let n=B(e,o,[`proxy-providers`],t,xt(t),{id:`mihomo-provider-create-${t}`,title:`Создать proxy-provider \`${t}\``,code:a,rangeFrom:p,rangeTo:m,family:`semantic`});n&&i.push(n)}return}if(a===`rule-provider-missing`&&s.length){let t=T(j(r,s)),n=ht(t),c=n.find(e=>!u.includes(e))||n[0]||``,l=P(c,u);if(c&&l&&l!==c){let n=pt(t);if(n.length>=2){n[1]=l;let t=V(e,o,s,n.join(`,`),{id:`mihomo-ruleset-replace-${s.join(`.`)}`,title:`Заменить rule-provider на \`${l}\``,code:a,isPreferred:!0,priority:90,rangeFrom:p,rangeTo:m,family:`semantic`});t&&i.push(t)}}if(c){let t=B(e,o,[`rule-providers`],c,bt(c),{id:`mihomo-ruleset-create-${c}`,title:`Создать rule-provider \`${c}\``,code:a,rangeFrom:p,rangeTo:m,family:`semantic`});t&&i.push(t)}return}if((a===`rule-target-missing`||a===`rule-target-not-found`)&&s.length){let t=pt(T(j(r,s))),n=mt(t),l=n>=0?T(t[n]):``,u=P(l,c,[`DIRECT`]);if(n>=0&&u&&u!==l){let r=t.slice();r[n]=u;let c=V(e,o,s,r.join(`,`),{id:`mihomo-rule-target-${s.join(`.`)}`,title:`Заменить target на \`${u}\``,code:a,isPreferred:!0,priority:90,rangeFrom:p,rangeTo:m,family:`semantic`});c&&i.push(c)}if(l&&!u){let t=dt(e,o,`proxy-groups`,St(l),{id:`mihomo-create-group-${l}`,title:`Создать proxy-group \`${l}\``,code:a,rangeFrom:p,rangeTo:m,family:`semantic`});t&&i.push(t)}return}if((a===`proxy-provider-missing-url`||a===`rule-provider-missing-url`||a===`proxy-provider-missing-path`||a===`rule-provider-missing-path`||a===`proxy-provider-missing-payload`||a===`rule-provider-missing-payload`||a===`proxy-provider-missing-interval-warning`||a===`rule-provider-missing-interval-warning`)&&s.length){let t=a.endsWith(`missing-url`)?`url`:a.endsWith(`missing-path`)?`path`:a.endsWith(`missing-payload`)?`payload`:`interval`,n=typeof s[s.length-1]==`string`?String(s[s.length-1]):``,r=T(s[0]),c=B(e,o,s,t,t===`url`?`https://example.invalid/${encodeURIComponent(n||`provider`)}.${r===`rule-providers`?`mrs`:`yaml`}`:t===`path`?`./providers/${(n||`provider`).replace(/[^A-Za-z0-9._-]+/g,`_`)}.${r===`rule-providers`?`mrs`:`yaml`}`:t===`payload`?[]:C,{id:`mihomo-provider-field-${s.join(`.`)}-${t}`,title:`Добавить поле \`${t}\``,code:a,isPreferred:t===`interval`,rangeFrom:p,rangeTo:m,family:`semantic`});c&&i.push(c);return}if(a.startsWith(`proxy-tls-`)&&s.length>=2){let t=ft(e,o,r,s.slice(0,-1),`tls`,!0,{id:`mihomo-proxy-tls-${s.join(`.`)}`,title:"Включить `tls: true`",code:a,isPreferred:!0,priority:85,rangeFrom:p,rangeTo:m,family:`semantic`});t&&i.push(t);return}if(a===`proxy-group-empty`&&s.length){let t=B(e,o,s,`proxies`,[`DIRECT`],{id:`mihomo-group-empty-${s.join(`.`)}`,title:"Добавить `proxies: [DIRECT]`",code:a,isPreferred:!0,priority:85,rangeFrom:p,rangeTo:m,family:`semantic`});t&&i.push(t);return}if(a===`proxy-group-missing-url`&&s.length){let t=B(e,o,s,`url`,S,{id:`mihomo-group-url-${s.join(`.`)}`,title:`Добавить \`url: ${S}\``,code:a,isPreferred:!0,priority:80,rangeFrom:p,rangeTo:m,family:`semantic`});t&&i.push(t);return}if(a===`proxy-servername-suggested`&&s.length>=2){let t=s.slice(0,-1),n=Ct(j(r,t));if(!n)return;let c=ft(e,o,r,t,`servername`,n,{id:`mihomo-servername-${s.join(`.`)}`,title:`Добавить \`servername: ${n}\``,code:a,isPreferred:!0,priority:80,rangeFrom:p,rangeTo:m,family:`semantic`});c&&i.push(c)}}),i}function Et(e){return e?typeof e==`function`?e:e&&typeof e.getQuickFixes==`function`?t=>e.getQuickFixes(t):null:null}function Dt(e,t){let n=Et(e);if(!n)return[];try{let e=n(t||{});return Array.isArray(e)?e:[]}catch{return[]}}function H(e={}){return{kind:`xray`,getQuickFixes(t={}){let n=w(t.text);if(!T(n))return[];let r=l(n);if(r==null)return[];let i=t.schema||null,a=it(e,t);return Ke([].concat(rt(n,r,a),nt(n,r,i)),t)}}}function U(e={}){return{kind:`mihomo`,getQuickFixes(e={}){let t=w(e.text);if(!T(t))return[];let n;try{n=m(t)}catch{n=void 0}if(n==null)return[];let r=e.schema||(e.yamlAssist&&typeof e.yamlAssist.getSchema==`function`?e.yamlAssist.getSchema():e.yamlAssist&&e.yamlAssist.schema?e.yamlAssist.schema:null);return Ke([].concat(Tt(t,n),wt(t,n,r)),e)}}}Object.freeze({applyTextEdits:Ue,applyQuickFixText:We,createXrayQuickFixProvider:H,createMihomoQuickFixProvider:U,getQuickFixesFromProvider:Dt});var W=Object.freeze({xray:`/static/schemas/xray-config.schema.json`,xrayRouting:`/static/schemas/xray-routing.schema.json`,xrayInbounds:`/static/schemas/xray-inbounds.schema.json`,xrayOutbounds:`/static/schemas/xray-outbounds.schema.json`,mihomo:`/static/schemas/mihomo-config.schema.json`}),G=new Map,K=Object.freeze({"xray-config":b(`xray-config`),"xray-routing":b(`xray-routing`),"xray-inbounds":b(`xray-inbounds`),"xray-outbounds":b(`xray-outbounds`),mihomo:je()}),Ot=Object.freeze({"xray-config":H(),"xray-routing":H(),"xray-inbounds":H(),"xray-outbounds":H(),mihomo:U()});function kt(e){return String(e||``).trim()}function q(e){return kt(e).toLowerCase()}function At(e){let t=kt(e).replace(/\\/g,`/`);if(!t)return``;let n=t.split(`/`);return n[n.length-1]||``}function J(e){let t=e||{};try{if(Object.prototype.hasOwnProperty.call(t,`expertModeEnabled`))return t.expertModeEnabled===!0}catch{}try{let e=window.XKeen&&window.XKeen.ui&&window.XKeen.ui.settings;if(e&&typeof e.isEditorExpertModeEnabled==`function`)return e.isEditorExpertModeEnabled();if(e&&typeof e.get==`function`){let t=e.get();return(t&&t.editor&&typeof t.editor==`object`?t.editor:{}).expertModeEnabled===!0}}catch{}return!1}function jt(e){let t=q(e);return t?t===`json`||t===`jsonc`||t===`application/json`||t===`application/jsonc`||t===`text/json`||t===`text/jsonc`:!0}function Y(e){let t=e||{},n=q(t.target||t.kind||t.feature||t.scope),r=At(t.file||t.filename||t.path||t.url||``),i=r.toLowerCase(),a=q(t.path||t.url||t.file||``),o=q(t.mode||t.language);return n===`inbounds`||/(^|_)inbounds/i.test(r)?`xray-inbounds`:n===`outbounds`||/(^|_)outbounds/i.test(r)?`xray-outbounds`:n===`routing`||/(^|_)routing/i.test(r)?`xray-routing`:n===`xray`||/(?:^|\.)jsonc?$/i.test(i)?`xray`:n===`mihomo`||i===`config.yaml`||i===`config.yml`||a.includes(`/mihomo/`)||o===`yaml`||o===`text/yaml`?`mihomo`:``}function Mt(e){let t=Y(e);if(!t)return null;if(t===`mihomo`)return{id:`mihomo`,family:`mihomo`,url:W.mihomo,title:`Mihomo config`,label:`Mihomo config`,mode:`yaml`};let n=t.startsWith(`xray-`)?t.slice(5):``,r={routing:W.xrayRouting,inbounds:W.xrayInbounds,outbounds:W.xrayOutbounds};return{id:n?`xray:${n}`:`xray`,family:`xray`,fragment:n,url:r[n]||W.xray,title:n?`Xray ${n} fragment`:`Xray config`,label:n?{routing:`Xray routing`,inbounds:`Xray inbounds`,outbounds:`Xray outbounds`}[n]||`Xray ${n}`:`Xray config`,mode:`json`}}async function Nt(e){let t=kt(e);if(!t)return null;if(G.has(t))return G.get(t);let n=fetch(t,{cache:`no-store`}).then(e=>{if(!e||!e.ok)throw Error(`schema load failed: ${t}`);return e.json()});G.set(t,n);try{return await n}catch(e){throw G.delete(t),e}}async function Pt(e){if(J(e))return{ok:!1,skipped:!0,reason:`expert-mode`,spec:null,schema:null};let t=Mt(e||{});if(!t)return{ok:!1,skipped:!0,reason:`schema-unmatched`,spec:null,schema:null};try{return{ok:!0,skipped:!1,spec:t,schema:await Nt(t.url)}}catch(e){return{ok:!1,skipped:!0,reason:`schema-load-failed`,error:e,spec:t,schema:null}}}function X(e){try{if(e&&e.runtime&&typeof e.runtime==`object`)return e.runtime}catch{}try{return window.XKeen&&window.XKeen.ui?window.XKeen.ui.cm6Runtime:null}catch{}return null}function Ft(e,t,n){let r=e&&e.raw?e.raw:e,i=X(n);try{if(i&&typeof i.setSchema==`function`)return!!i.setSchema(r,t||null)}catch{}try{if(r&&typeof r.setSchema==`function`)return!!r.setSchema(t||null)}catch{}return!1}function Z(e,t,n){let r=e&&e.raw?e.raw:e,i=X(n);try{if(i&&typeof i.setSnippetProvider==`function`)return!!i.setSnippetProvider(r,t||null)}catch{}try{if(r&&typeof r.setSnippetProvider==`function`)return!!r.setSnippetProvider(t||null)}catch{}try{if(r&&typeof r.setOption==`function`)return!!r.setOption(`snippetProvider`,t||null)}catch{}return!1}function It(e,t,n){let r=e&&e.raw?e.raw:e,i=X(n);try{if(i&&typeof i.setQuickFixProvider==`function`)return!!i.setQuickFixProvider(r,t||null)}catch{}try{if(r&&typeof r.setQuickFixProvider==`function`)return!!r.setQuickFixProvider(t||null)}catch{}try{if(r&&typeof r.setOption==`function`)return!!r.setOption(`quickFixProvider`,t||null)}catch{}return!1}function Lt(e,t,n){let r=e&&e.raw?e.raw:e,i=X(n);try{if(i&&typeof i.setSemanticValidation==`function`)return!!i.setSemanticValidation(r,t||null)}catch{}try{if(r&&typeof r.setSemanticValidation==`function`)return!!r.setSemanticValidation(t||null)}catch{}try{if(r&&typeof r.setOption==`function`)return!!r.setOption(`semanticValidation`,t||null)}catch{}return!1}function Q(e){let t=q(e);return t?t===`xray`?`xray-config`:t:``}function Rt(e){if(J(e))return null;let t=e||{},n=Q(t.snippetKind||t.schemaKind);if(n&&K[n])return K[n];let r=Q(Y(t));return r&&K[r]||null}function zt(e){if(J(e))return null;let t=e||{},n=Q(t.quickFixKind||t.schemaKind);if(n&&Ot[n])return Ot[n];let r=Q(Y(t));return r&&Ot[r]||null}function Bt(e){if(J(e))return null;let t=e||{},n=Q(t.semanticKind||t.schemaKind)||Q(Y(t));return n&&(n===`xray-config`||n===`xray`||n===`xray-routing`||n===`xray-inbounds`||n===`xray-outbounds`)?{kind:n===`xray`?`xray-config`:n,options:{schemaKind:n}}:null}function $(e,t){let n=e&&e.raw?e.raw:e,r=t||{},i=Ft(n,null,r),a=Z(n,null,r),o=It(n,null,r),s=Lt(n,null,r);return i||a||o||s}async function Vt(e,t){let n=e&&e.raw?e.raw:e;if(!n)return{ok:!1,skipped:!0,reason:`editor-missing`};let r=t||{};if(J(r))return $(n,r),{ok:!1,skipped:!0,reason:`expert-mode`};let i=Mt(r);if(!i)return $(n,r),{ok:!1,skipped:!0,reason:`schema-unmatched`};if(!jt(r.mode||r.language||i.mode))return $(n,r),{ok:!1,skipped:!0,reason:`mode-not-json`,spec:i};let a=await Pt(r);if(!a||!a.ok||!a.schema)return $(n,r),{ok:!1,skipped:!0,reason:a&&a.reason?a.reason:`schema-load-failed`,error:a&&a.error?a.error:null,spec:i};let o=Ft(n,a.schema,r),s=Rt({...r,schemaKind:i.family===`xray`?i.fragment?`xray-${i.fragment}`:`xray-config`:i.family}),c=r.quickFixProvider||zt({...r,schemaKind:i.family===`xray`?i.fragment?`xray-${i.fragment}`:`xray-config`:i.family}),l=r.semanticValidation||Bt({...r,schemaKind:i.family===`xray`?i.fragment?`xray-${i.fragment}`:`xray-config`:i.family}),u=Z(n,s,r),d=It(n,c,r),f=Lt(n,l,r);return{ok:o||u||d||f,skipped:!1,spec:i,schema:a.schema,snippetProvider:s,quickFixProvider:c,semanticValidation:l}}Object.freeze({resolveEditorSchemaSpec:Mt,resolveEditorSnippetProvider:Rt,resolveEditorQuickFixProvider:zt,resolveEditorSemanticValidation:Bt,loadEditorSchema:Pt,applySchemaToEditor:Vt,clearSchemaFromEditor:$,setEditorSnippetProvider:Z,setEditorQuickFixProvider:It,setEditorSemanticValidation:Lt});export{U as a,Rt as i,$ as n,H as o,Pt as r,Vt as t};