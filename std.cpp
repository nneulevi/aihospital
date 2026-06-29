#include <bits/stdc++.h>
using namespace std;

struct Solver {
    int n, m;
    int tot;
    vector<vector<int>> g;
    vector<int> indeg;
    vector<int> outRoot, inRoot;

    Solver(int n, int m) : n(n), m(m) {
        tot = n;
        g.resize(9 * n + 5);
        indeg.assign(9 * n + 5, 0);
        outRoot.assign(4 * n + 5, 0);
        inRoot.assign(4 * n + 5, 0);
    }

    int newNode() {
        ++tot;
        if (tot >= (int)g.size()) {
            g.resize(tot + 5);
            indeg.resize(tot + 5, 0);
        }
        return tot;
    }

    void addEdge(int u, int v) {
        g[u].push_back(v);
        ++indeg[v];
    }

    void buildOut(int p, int l, int r) {
        outRoot[p] = newNode();
        if (l == r) {
            addEdge(outRoot[p], l);
            return;
        }
        int mid = (l + r) >> 1;
        buildOut(p << 1, l, mid);
        buildOut(p << 1 | 1, mid + 1, r);
        addEdge(outRoot[p], outRoot[p << 1]);
        addEdge(outRoot[p], outRoot[p << 1 | 1]);
    }

    void buildIn(int p, int l, int r) {
        inRoot[p] = newNode();
        if (l == r) {
            addEdge(l, inRoot[p]);
            return;
        }
        int mid = (l + r) >> 1;
        buildIn(p << 1, l, mid);
        buildIn(p << 1 | 1, mid + 1, r);
        addEdge(inRoot[p << 1], inRoot[p]);
        addEdge(inRoot[p << 1 | 1], inRoot[p]);
    }

    void addPointToRange(int p, int l, int r, int ql, int qr, int u) {
        if (ql > qr) return;
        if (ql <= l && r <= qr) {
            addEdge(u, outRoot[p]);
            return;
        }
        int mid = (l + r) >> 1;
        if (ql <= mid) addPointToRange(p << 1, l, mid, ql, qr, u);
        if (qr > mid) addPointToRange(p << 1 | 1, mid + 1, r, ql, qr, u);
    }

    void addRangeToPoint(int p, int l, int r, int ql, int qr, int u) {
        if (ql > qr) return;
        if (ql <= l && r <= qr) {
            addEdge(inRoot[p], u);
            return;
        }
        int mid = (l + r) >> 1;
        if (ql <= mid) addRangeToPoint(p << 1, l, mid, ql, qr, u);
        if (qr > mid) addRangeToPoint(p << 1 | 1, mid + 1, r, ql, qr, u);
    }

    vector<int> solve() {
        buildOut(1, 1, n);
        buildIn(1, 1, n);

        for (int q = 0; q < m; ++q) {
            int op, i, j, k;
            cin >> op >> i >> j >> k;

            if (op == 0) {
                addPointToRange(1, 1, n, i, j - 1, j);
                addPointToRange(1, 1, n, j + 1, k, j);
            } else {
                addRangeToPoint(1, 1, n, i, j - 1, j);
                addRangeToPoint(1, 1, n, j + 1, k, j);
            }
        }

        queue<int> que;
        for (int i = 1; i <= tot; ++i) {
            if (indeg[i] == 0) que.push(i);
        }

        vector<int> order;
        order.reserve(tot);
        while (!que.empty()) {
            int u = que.front();
            que.pop();
            order.push_back(u);
            for (int v : g[u]) {
                if (--indeg[v] == 0) que.push(v);
            }
        }

        if ((int)order.size() != tot) return {};

        vector<int> ans(n + 1, 0);
        int val = 1;
        for (int u : order) {
            if (1 <= u && u <= n) ans[u] = val++;
        }
        return ans;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;

    Solver solver(n, m);
    vector<int> ans = solver.solve();

    if (ans.empty()) {
        cout << -1 << '\n';
        return 0;
    }

    for (int i = 1; i <= n; ++i) {
        if (i > 1) cout << ' ';
        cout << ans[i];
    }
    cout << '\n';

    return 0;
}
