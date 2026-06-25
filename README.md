# MusicScript
用代码编写midi音乐的DSL，设计哲学是像配备粗细两种准焦螺旋一样，随时在不同封装层级控制音乐，既像平时谱曲一样自然，又像平时写代码一样可编程，如此一来，MusicScript会是算法作曲的又一个好选择，
虽然我是业余学编程的（才学了半年），不懂什么叫图灵完备，但我只告诉你一件事，MusicScript能嵌入任意python代码！

## 顶层语句
### track
```
track <name>;
track <name> <attr>=<val>;
track <name> <attr>=<val> <attr>=<val> ...;
```
track加轨道名加零到多个属性，最后加分号，以此定义一个轨道，属性有key（默认0）, len（默认1）, vel（默认100）, hook（默认None）。
```
drum track <name> <attr>=<val> ...;
```
前面追加drum关键字，即可定义鼓轨道，这时属性在这个基础上少了key。
### score
```
score <name> <attr>=<val> ... { ... }
```
score加乐谱名加零到多个属性，再加花括号包裹的音符区（后续会提），以此定义一个乐谱，属性有key（默认0）, unit（默认1）, vel（默认100）, hook（默认None）
### template
