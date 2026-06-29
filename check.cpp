#include <bits/stdc++.h>

template<class T, class Op>
struct ST
{
	//static_assert(std::is_convocable_r_v<T, Op, T, T>, "Op must be a binary function object that returns T and takes two T arguments");
	//static_assert(std::is_copy_constructible_v<Op> or std::is_move_constructible_v<Op>, "Op must be default constructible");
	int n;
	std::vector<T> a;
	std::vector<std::array<T, 20>> st;
	Op op;
    ST() {}
	ST(size_t n, const Op& o, const std::vector<T>& other) :n(n), op(o), a(other) {
		st.resize(n);
		for (int i = 0; i < n; i++) st[i][0] = a[i];
		for (int j = 1; j < 20; j++)
			for (int i = 1; i + (1 << j) <= n; i++)
				st[i][j] = op(st[i][j - 1], st[i + (1 << (j - 1))][j - 1]);
	}
	T query(int l, int r)
	{
		if (l > r) throw std::invalid_argument("ERROR");
		int k = Log[r - l + 1];
		return op(st[l][k], st[r - (1 << k) + 1][k]);
	}
};

struct checker
{
    std::vector<int> ans, std_ans;
    std::vector<std::array<int,4>> constrains;
    int n, m;
    int mn(int x, int y) {return std::min(x, y);}
    int mx(int x, int y) {return std::max(x, y);}
    ST<int, decltype(mn)> st_mn;
    ST<int, decltype(mx)> st_mx;
    checker(int _n, int _m, const std::vector<int>& _ans, const std::vector<int>& _std_ans) : n(_n), m(_m), ans(_ans), std_ans(_std_ans) {
        st_mn = ST<int, decltype(mn)>(n, mn, ans);
        st_mx = ST<int, decltype(mx)>(n, mx, ans);
    }
    bool check_permutation(){
        std::vector<bool> vis(n + 1, false);
        for (int i = 0; i < n; i++) {
            if (ans[i] < 1 || ans[i] > n || vis[ans[i]]) return false;
            vis[ans[i]] = true;
        }
        return true;
    }
    bool check_constraint(){
        for (const auto& [op, i, j, k] : constrains) {
            if (!op){
                if (ans[j] != st_mn.query(i, k)) return false;
            }
            else{
                if (ans[j] != st_mx.query(i, k)) return false;
            }
        }
        return true;
    }
    bool check(){
        if(std_ans[0] != -1 and ans[0] == -1) return false;
        if(!check_permutation()) return false;
        if(!check_constraint()) return false;
        return true;
    }
};