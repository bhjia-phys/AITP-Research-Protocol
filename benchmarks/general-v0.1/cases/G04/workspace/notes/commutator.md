# 逐元素求解与核中的自由度

本推导使用
$H_0=\operatorname{diag}(0,1)$，
$B_0=\begin{pmatrix}0&1\\-1&0\end{pmatrix}$。
完整输入和一个直接检查保存在[原始验证记录](../data/original-check.txt)。

写 $E_1=0,E_2=1$，方程逐元素为

$$
(E_m-E_n)X_{mn}=(B_0)_{mn}.
$$

非对角元给出 $X_{12}=X_{21}=-1$。
对角方程为 $0=(B_0)_{11}=(B_0)_{22}$，在该输入上成立。
故所有解为

$$
X=\begin{pmatrix}a&-1\\-1&b\end{pmatrix},\qquad a,b\in\mathbb R.
$$

自由的对角部分与 $H_0$ 对易。这一计算完整解决了上述 $B_0$ 输入的问题；
其对研究问题的解释见[主笔记](../research.md)。
