rm original.eti compare.eti

./mux-throttled-nofb.sh -n 10 > original.eti
../crc-dabmux-0.3.0.4/src/CRC-DabMux-cfg examplemux.config > compare.eti

dhex original.eti compare.eti
