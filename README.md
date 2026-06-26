# MusicScript
<img width="587" height="557" alt="ms" src="https://github.com/user-attachments/assets/f22ba2db-325f-4b9d-bfee-11111183b521" />

用代码编写midi音乐的DSL，设计哲学是像配备粗细两种准焦螺旋一样，随时在不同封装层级控制音乐，既像平时谱曲一样自然，又像平时写代码一样可编程，如此一来，MusicScript会是算法作曲的又一个好选择，
虽然我是业余学编程的（才学了半年），不知道图灵完备的确切定义是什么，但我只告诉你一件事，MusicScript能嵌入任意python代码！
# 开发小故事（不闲得慌就别看）
由于我天怒人怨的项目设计能力，光鲜亮丽的DSL语法背后是不尊重代码文本原始内容的AST；是构造参数部分传入None占位，去不同模块溜达一圈才完成最终初始化的对象；是两段相似度90%的各100行左右的代码；
是取不出来名字就起名叫“取不出来”的变量名。在我怀疑我是不是被逼到要先用笔和纸打草稿把DSL语法逻辑理清再动工时，我毅然决然选择想到哪写到哪，这导致项目混乱难以扩展，导致我在想出某些想法时实现的复杂度把他它们扼杀了，
如果哪天太阳从西边出来，我会重写它，再慢慢实现没能实现的想法。不过，不管怎么说，MusicScript的设计哲学是空前正确的。
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
score加乐谱名加零到多个属性，再加花括号包裹的音符区（后续会提），以此定义一个乐谱，属性有key（默认0）, unit（默认1）, vel（默认100）, hook（默认None）。
### template
```
template <name> beats=... notes=... { ... }
```
template加模板名加固定的beats，notes两个属性，再加花括号包裹的音符区，以此定义一个模板，beats和notes都是正整数。
```
early template <name> beats=... notes=... { ... }
```
前面追加early关键字，即可定义提前模板。
### 内联python
```
`<python>`
```
反引号内包裹任意不含反引号的python代码（换行符可以包裹）。
```
`
def hello():
  print('hello world')
__export__ = ['hello']
`
```
用__export__把变量导出到MusicScript的作用域中。
## 音符区
由加号、乘号、轨道使用、乐谱引用组成。
```
{
track1: 1 2 3 *
track2: 1 2 3
+
score1 *
score2 *
track3
}
```
轨道使用和乐谱引用是加号乘号所操作的目标，加号表示衔接，乘号表示叠加。
### 轨道使用
```
<name> <attr>=<val> ... : <note_or_chord> <note_or_chord> ...
```
在指定轨道上编写音符与和弦，轨道名后的零到多个属性可作为临时属性覆盖原属性
### 乐谱引用
```
<name> <attr>=<val> ...
```
引用定义的其他乐谱，同样支持临时属性
### 音符
可选的`<python_code>`  可选的零到多个.或零到多个'  可选的零到多个s或零到多个f  必选的0-7数字  可选的零到多个-  可选的零到多个_
如`func`''f2---__，这是一个及其复杂的例子
