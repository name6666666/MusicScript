{% include 'kit.ms' %}

track _mel instr=10 vel=127 key=12;
track _acc instr=10 vel=80;

score _b unit=$bpm(140) {
    _mel: 1 2 | 3 2 3 '1 | 7- 5- | 6 5 5 4 | 3- 2 3 *
    _acc: 0 0 | `rc`$min(6)--- | `rc`$maj(5)--- | `rc`$maj(4)--- | `rc`$min(3)---
    +
    _mel len=`1/4`: 4--- 3-43 2--- 4--- *
    _acc: `rc`$min(2)---
    +
    _mel: 3- 1- | 3 s4 s5 '1 | 7- 1 2 *
    _acc: `rc`$min(.6)--- | `rc`$maj(.s6)--- | `rc`$dom7(3)---
    +
    _mel: 3 2 3 '1 | 7- 5- | 6 5 5 4 | 3- 2 3 *
    _acc: `rc`$min(6)--- | `rc`$maj(5)--- | `rc`$maj(4)--- | `rc`$min(3)---
    +
    _mel len=`1/4`: 4--- 3-43 2--- 4--- *
    _acc: `rc`$min(2)---
    +
    _mel: 3- 1- | 3 2 1 .7 | .6 *
    _acc: `rc`$min(.6)--- | `rc`$maj(.3)--- | `rc`$min(.6)---
}

score _a unit=$bpm(140) {
    _mel: 3- 2 1 | 2- .7- | 1 .7 .7 .6 | .5--- *
    _acc: $min(6)--- | $maj(5)--- | $maj(4)--- | $maj(3)---
    +
    _mel: 4- 3 2 | 3- 1- | .7 1 2 4 | 3--- *
    _acc: $min(2)--- | $maj(1)--- | $maj(.7)--- | $maj(3)---
}

score example {
    _b + _a + _b key=2
}
