# RouterOS template for Unified UI MikroTik container.
# Fill placeholders before import. Do NOT commit real secrets.

:local CONTAINER_FILE "unified-ui-mikrotik-docker-archive.tar.gz"
:local CONTAINER_ROOT "/usb1/docker/unified-ui-mikrotik"
:local CONTAINER_IP "192.168.254.3/24"
:local GATEWAY_IP "192.168.254.1"
:local SUB_URL "<MIHOMO_SUBSCRIPTION_URL>"
:local AUTH_USER "<UI_USER>"
:local AUTH_PASSWORD "<UI_PASSWORD>"
:local SECRET_KEY "<UI_SECRET_KEY>"

/system backup save name=pre-unified-ui-mikrotik
/export file=pre-unified-ui-mikrotik

:foreach c in=[/container find where comment="mihomo-mikrotik"] do={ /container/stop $c; :delay 5; /container/remove $c }
:foreach c in=[/container find where name~"mihomo-mikrotik"] do={ /container/stop $c; :delay 5; /container/remove $c }
:foreach c in=[/container find where comment="unified-ui-mikrotik"] do={ /container/stop $c; :delay 5; /container/remove $c }

:foreach e in=[/container/envs find where list="MIHOMO"] do={ /container/envs/remove $e }
:foreach e in=[/container/envs find where list="UNIFIED_UI_MIKROTIK"] do={ /container/envs/remove $e }
:foreach n in=[/ip/firewall/nat find where comment~"mihomo|unified-ui-mikrotik"] do={ /ip/firewall/nat/remove $n }
:foreach a in=[/ip/address find where comment~"mihomo|unified-ui-mikrotik"] do={ /ip/address/remove $a }
:foreach v in=[/interface/veth find where name="MIHOMO"] do={ /interface/veth/remove $v }
:foreach f in=[/file find where name="usb1/docker/mihomo-mikrotik"] do={ /file/remove $f }
:foreach f in=[/file find where name="usb1/docker/unified-ui-mikrotik"] do={ /file/remove $f }

/interface/veth add name=MIHOMO address=$CONTAINER_IP gateway=$GATEWAY_IP comment="unified-ui-mikrotik"
/ip/address add address=($GATEWAY_IP . "/24") interface=MIHOMO comment="unified-ui-mikrotik"
/ip/firewall/nat add chain=srcnat action=masquerade src-address=192.168.254.0/24 comment="unified-ui-mikrotik"
/ip/firewall/nat add chain=dstnat action=dst-nat protocol=tcp dst-address=172.16.0.22 dst-port=8088 to-addresses=192.168.254.3 to-ports=8088 comment="unified-ui-mikrotik-ui"
/ip/firewall/nat add chain=dstnat action=dst-nat protocol=tcp dst-address=172.16.0.22 dst-port=9090 to-addresses=192.168.254.3 to-ports=9090 comment="unified-ui-mikrotik-api"

/container/envs add list=UNIFIED_UI_MIKROTIK key=UNIFIED_UI_AUTH_USER value=$AUTH_USER
/container/envs add list=UNIFIED_UI_MIKROTIK key=UNIFIED_UI_AUTH_PASSWORD value=$AUTH_PASSWORD
/container/envs add list=UNIFIED_UI_MIKROTIK key=UNIFIED_UI_SECRET_KEY value=$SECRET_KEY
/container/envs add list=UNIFIED_UI_MIKROTIK key=MIHOMO_SUB_URL value=$SUB_URL
/container/envs add list=UNIFIED_UI_MIKROTIK key=MIHOMO_ENABLE_TUN value=false
/container/envs add list=UNIFIED_UI_MIKROTIK key=MIHOMO_MIXED_PORT value=1080
/container/envs add list=UNIFIED_UI_MIKROTIK key=MIHOMO_DNS_PORT value=1053

/container/add file=$CONTAINER_FILE interface=MIHOMO root-dir=$CONTAINER_ROOT envlist=UNIFIED_UI_MIKROTIK hostname=unified-ui-mikrotik logging=yes start-on-boot=yes dns=1.1.1.1,8.8.8.8,9.9.9.9 comment="unified-ui-mikrotik"
/container/start [find where comment="unified-ui-mikrotik"]

# After first successful boot, remove sensitive env vars because RouterOS logs env on container start.
#:foreach e in=[/container/envs find where list="UNIFIED_UI_MIKROTIK" and key="UNIFIED_UI_AUTH_PASSWORD"] do={ /container/envs/remove $e }
#:foreach e in=[/container/envs find where list="UNIFIED_UI_MIKROTIK" and key="UNIFIED_UI_SECRET_KEY"] do={ /container/envs/remove $e }
#:foreach e in=[/container/envs find where list="UNIFIED_UI_MIKROTIK" and key="MIHOMO_SUB_URL"] do={ /container/envs/remove $e }
