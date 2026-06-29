Description:
a graph with n
 vertices and n−1
 edges, and there is exactly one path between any two vertices. Formally, the regions form a tree.

Each region has a friendliness value ai
.

There are q
 queries. In each query, you are given two vertices x
 and y
 (x≠y)
. Consider the shortest path from vertex x
 to vertex y
 in the tree. Let the vertices v1,v2,…,vk
 form this path, where v1=x
, vk=y
. You need to find the number of subsegments of this path for which the following condition holds:
avl⊕avl+1⊕…⊕avr≥(avl+avl+1+…+avr),
where 1≤l≤r≤k
 — the boundaries of the subsegment of vertices on the path from x
 to y
.
Input
Each test consists of multiple test cases. The first line contains a single integer t
 (1≤t≤1e4
) — the number of test cases. Then the descriptions of the test cases follow.

The first line of each test case contains integers n
 (2≤n≤1e5
) — the number of vertices in the tree, and q
 (1≤q≤1e5
) — the number of queries.

The second line contains an array of n
 non-negative integers — the friendliness values of the regions (0≤ai<2^20
).

The next n−1
 lines describe the edges of the tree: each line contains integers u,v
 (1≤u,v≤n
) — an edge.

Then q
 lines follow describing the queries. Each query is given by integers x,y
 (1≤x,y≤n
, x≠y
) — the vertices that define the path for which you need to count the number of hospitable subsegments.

It is guaranteed that the sum of n
 and the sum of q
 over all test cases do not exceed 1e5
, and that the edges indeed form a tree.


Sol:

首先注意到，对非负整数恒有

$$
a_{v_l}\oplus a_{v_{l+1}}\oplus\cdots\oplus a_{v_r}
\le
a_{v_l}+a_{v_{l+1}}+\cdots+a_{v_r}.
$$

所以题目中的条件

$$
a_{v_l}\oplus a_{v_{l+1}}\oplus\cdots\oplus a_{v_r}
\ge
a_{v_l}+a_{v_{l+1}}+\cdots+a_{v_r}
$$

等价于两边相等。也就是说，这个子段中任意一个二进制位不能在两个不同点的权值中同时出现；否则加法会产生进位，异或值就会小于和。

由于 $a_i<2^{20}$，每个合法子段中最多只会引入 $20$ 个不同的非零二进制位，但权值为 $0$ 的点可以有很多个，需要额外压缩处理。

将树以 $1$ 为根，记深度为 $dep_u$。对每个点 $u$，定义

$$
lim_u
$$

表示从 $u$ 往祖先方向走时，使得路径 $lim_u\sim u$ 合法的最浅深度。也就是说，对于任意祖先 $p$：

- 若 $dep_p\ge lim_u$，则路径 $p\sim u$ 合法；
- 若 $dep_p<lim_u$，则路径 $p\sim u$ 不合法。

求 $lim_u$ 可以在一次 DFS 中完成。维护当前根到 DFS 栈路径上，每个二进制位最近两次出现的位置。对于点 $u$，如果某个二进制位在根到 $u$ 的路径上至少出现了两次，设这个二进制位倒数第二次出现的深度为 $d$，那么合法后缀的起点深度必须大于 $d$。因此

$$
lim_u=\max(1,\max(d+1)).
$$

这里对 $20$ 个二进制位取最大值即可。

一个重要性质是：沿着根到叶子的方向，$lim_u$ 单调不降。因为路径往下多加入一个点，只可能让某些二进制位的倒数第二次出现位置变深，不可能变浅。

接下来考虑一次询问 $(x,y)$。设

$$
l=LCA(x,y).
$$

先统计完全位于 $x\to l$ 这条祖先链内的合法子段。枚举子段的较深端点 $i$，它的较浅端点必须在深度区间

$$
[\max(dep_l,lim_i), dep_i]
$$

中，因此贡献为

$$
dep_i-\max(dep_l,lim_i)+1.
$$

由于 $lim$ 在祖先链上单调，存在一个临界点 $p$，使得：

- $x\to p$ 这一段中的点满足 $lim_i\ge dep_l$，贡献使用 $lim_i$；
- $fa_p\to l$ 这一段中的点满足 $lim_i<dep_l$，贡献使用 $dep_l$。

这个临界点可以用倍增在 $O(\log n)$ 内找到。

预处理两个根路径前缀和：

$$
pre_1(u)=\sum_{i\in root\to u} dep_i,
$$

$$
pre_2(u)=\sum_{i\in root\to u}(dep_i-lim_i+1).
$$

于是祖先链 $u\to anc$ 内的答案可以写成一个函数 `calc(u, anc)`：

1. 找到最高的点 $p$，满足 $p$ 在 $u\to anc$ 上且 $lim_p\ge dep_{anc}$。
2. 对 $u\to p$ 使用 $pre_2$ 求和。
3. 对 $fa_p\to anc$ 使用 $pre_1$ 求

$$
\sum (dep_i-dep_{anc}+1).
$$

如果不存在这样的 $p$，则整条链都属于第 3 类；如果 $p=anc$，则第 3 类为空。

同理可以得到完全位于 $y\to l$ 的合法子段。注意单点 $l$ 被计算了两次，所以基础答案为

$$
calc(x,l)+calc(y,l)-1.
$$

剩下只需要统计跨过 $l$ 的子段，也就是同时包含 $l$ 左右两侧至少一个点的子段。

对一侧，例如 $l\to x$，我们把所有满足路径 $l\sim p$ 合法的端点 $p$ 按路径异或值，也等价于按路径 bitwise-or 值，压缩成若干组：

$$
(mask,cnt).
$$

其中 $mask$ 是路径 $l\sim p$ 中出现过的二进制位集合，$cnt$ 是得到这个 $mask$ 的端点个数。注意这里不包含 $p=l$，因为跨越 $l$ 的子段要求两侧都至少选一个点。

压缩方法如下：

从 $l$ 的儿子方向向 $x$ 走，当前已经拥有的二进制集合为 $mask$，初始为 $a_l$。设当前还没有处理的位置深度为 $d$。

每一步同时找两个位置：

- $bad$：从深度 $d$ 开始，第一个满足 $(a_u\&mask)\ne 0$ 的点。这个点会造成重复二进制位。
- $add$：从深度 $d$ 开始，第一个满足 $(a_u\&\sim mask)\ne 0$ 的点。这个点会引入新的二进制位。

若 $bad$ 更靠前，或者 $bad=add$，则在 $bad$ 之前的零权值点都对应当前 $mask$，统计完后停止。若 $add$ 更靠前，则 $d\sim fa_{add}$ 之间的零权值点都对应当前 $mask$，然后把 $add$ 这个点计入新的 $mask|a_{add}$，并继续向下处理。

每次 $mask$ 至少增加一个二进制位，因此一侧最多产生 $21$ 组。查找“从当前深度开始，第一个权值与某个 bit 集合有交的点”可以用重链剖分加线段树维护区间 OR 完成，复杂度 $O(\log^2 n)$；也可以用每个 bit 的根路径前缀计数配合二分完成。

分别得到左右两侧的压缩数组 $A,B$ 后，跨越 $l$ 的贡献为

$$
\sum_{(m_1,c_1)\in A}\sum_{(m_2,c_2)\in B}
[\, (m_1\&m_2)=a_l\,]\cdot c_1c_2.
$$

因为两边路径都包含 $l$，所以它们公共的二进制位只能来自 $a_l$ 本身；除此之外若还有公共 bit，就说明跨越后的整段中该 bit 出现了至少两次，不合法。

综上，一次询问答案为

$$
calc(x,l)+calc(y,l)-1+cross(x,y,l).
$$

复杂度：

- 预处理 $lim$、倍增、前缀和、重链剖分：$O(n\log n)$。
- 每次询问两次 `calc`：$O(\log n)$。
- 跨越 LCA 的部分每侧最多扩展 $20$ 次，每次查找 $O(\log^2 n)$，最后枚举组对最多 $21^2$，所以单次询问复杂度为 $O(20\log^2 n+20^2)$。

已有思路中“单侧路径贡献”这一部分是正确的，但需要明确 $top/lim$ 存的是深度还是点，并补上 $lim$ 单调性的证明；另外跨越 LCA 的子段不能被两条单侧链覆盖，需要单独按二进制集合压缩统计。
