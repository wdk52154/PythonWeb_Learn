# 新闻资讯项目：前端 CRUD 流程

本文只说明前端如何完成增删改查，不展开 FastAPI 内部的数据库实现。代码范围主要是：

```text
news-headline-frontend/
├── src/views/                 # 页面：接收操作、展示数据
├── src/components/            # 组件：新闻列表项等
├── src/store/                 # Pinia：状态管理和接口请求
│   ├── user.js
│   └── modules/
│       ├── news.js
│       ├── favorite.js
│       └── history.js
├── src/config/api.js          # 后端 API 基地址
└── src/router/index.js        # 页面路由
```

## 1. 前端整体调用链

```text
用户点击、提交表单或进入页面
  ↓
Vue 页面 / 组件
  ↓ 调用 Store action
Pinia Store 组织参数、调用 Axios
  ↓ HTTP 请求
FastAPI 后端接口
  ↓ JSON 响应
Store 判断 response.data.code
  ↓
更新 Pinia state / localStorage
  ↓
Vue 响应式刷新页面
```

前端接口基地址配置在 `src/config/api.js`：

```js
export const apiConfig = {
  baseURL: 'http://127.0.0.1:8000',
}
```

页面不直接拼装数据库逻辑，也不直接维护多处重复的请求状态。页面负责交互，Store 负责请求和状态，组件负责展示。

## 2. 一次前端请求的通用流程

以“添加收藏”为例：

```text
NewsDetail.vue 点击星标
  -> toggleFavorite()
  -> favoriteStore.toggleFavorite(news)
  -> favoriteStore.addFavoriteApi(news.id)
  -> axios.post('/api/favorite/add', { newsId })
  -> 收到 { code: 200, data: ... }
  -> favoriteStore.addFavorite(news)
  -> 更新 favorites
  -> 保存 localStorage
  -> 页面上的星标和收藏列表自动刷新
```

Store 中常见的请求模板：

```js
async someAction(data) {
  this.loading = true

  try {
    const response = await axios.post(
      `${apiConfig.baseURL}/api/example`,
      data,
      { headers: { Authorization: userStore.token } }
    )

    if (response.data && response.data.code === 200) {
      // 更新 Pinia state
      return { success: true, data: response.data.data }
    }

    return {
      success: false,
      message: response.data.message || '操作失败'
    }
  } catch (error) {
    return { success: false, message: '网络请求失败' }
  } finally {
    this.loading = false
  }
}
```

页面收到 Store 返回值后，再负责 Toast、Dialog、跳转和空状态显示。

## 3. Create：前端新增数据

前端的“新增”主要有三种业务：注册用户、添加收藏、添加浏览历史。

### 3.1 注册用户

页面：`src/views/Register.vue`

```text
用户填写 username、password、confirmPassword
  -> Vant 表单校验
  -> onSubmit()
  -> userStore.register({ username, password })
  -> POST /api/user/register
```

请求体：

```json
{
  "username": "new_user",
  "password": "123456"
}
```

成功后，`userStore.register` 从响应中读取：

```js
const userInfo = response.data.data.userInfo
const token = response.data.data.token

this.userInfo = userInfo
this.token = token
this.isLogin = true
```

页面随后跳转到首页。确认密码只在前端校验，不会发送给后端。

### 3.2 添加收藏

页面：`src/views/NewsDetail.vue`

```text
点击收藏按钮
  -> 先判断 userStore.getLoginStatus
  -> 未登录：提示并跳转 /login
  -> 已登录：favoriteStore.toggleFavorite(news)
```

Store：`src/store/modules/favorite.js`

```js
const response = await axios.post(
  `${apiConfig.baseURL}/api/favorite/add`,
  { newsId },
  {
    headers: {
      Authorization: userStore.token
    }
  }
)
```

接口成功后：

1. `toggleFavorite` 调用 `addFavorite(news)`。
2. 新闻对象被放入 `favorites` 数组的最前面。
3. `saveFavorites()` 将列表写入 `localStorage`。
4. `isFavorite(news.id)` 的计算结果发生变化，详情页星标自动更新。

### 3.3 添加浏览历史

页面：`src/views/NewsDetail.vue` 在详情读取成功后调用：

```text
historyStore.addHistoryApi(newsStore.newsDetail.id)
  -> POST /api/history/add
  -> Body: { newsId: <新闻 ID> }
```

只有登录用户会调用后端历史接口。未登录场景下，Store 中也提供 `addHistory(news)`，可以将历史保存到 `localStorage`，但当前详情页的调用主要走后端 API。

## 4. Read：前端查询数据

### 4.1 查询新闻分类

页面：`src/views/Home.vue`

```text
onMounted()
  -> newsStore.getCategories()
  -> GET /api/news/categories
  -> response.data.data
  -> newsStore.categories = 分类数组
```

请求成功后，Store 额外添加一个前端虚拟分类“更多”，它不是数据库中的真实分类。

请求失败时，`newsStore.getCategories` 会写入一组默认分类，使页面仍可以显示分类导航。

### 4.2 查询新闻列表

Store：`src/store/modules/news.js`

```js
const params = {
  categoryId: this.currentCategory,
  page: isRefresh ? 1 : Math.ceil(this.newsList.length / 10) + 1,
  pageSize: 10
}

const response = await axios.get(
  `${apiConfig.baseURL}/api/news/list`,
  { params }
)
```

三种页面操作对应三种查询状态：

| 页面操作 | Store 行为 |
| --- | --- |
| 首次进入 | 查询当前分类第 1 页 |
| 下拉刷新 | 清空 `newsList`，重新查询第 1 页 |
| 上拉加载 | 查询下一页，并将数据追加到 `newsList` |
| 切换分类 | 修改 `currentCategory`，清空旧列表，重新查询 |

返回成功后：

```js
const newsData = response.data.data.list
this.newsList = isRefresh
  ? newsData
  : [...this.newsList, ...newsData]

if (newsData.length < params.pageSize) {
  this.finished = true
}
```

页面通过 `newsStore.loading`、`newsStore.refreshing` 和 `newsStore.finished` 控制 Vant 列表组件的加载、刷新和“没有更多”状态。

### 4.3 查询新闻详情

页面：`src/views/NewsDetail.vue`

```text
路由 /news/detail/:id
  -> 读取 route.params.id
  -> newsStore.getNewsDetail(id)
  -> GET /api/news/detail?id=<id>
  -> newsStore.newsDetail = response.data.data
```

详情页面根据 `newsDetail` 展示标题、作者、发布时间、正文、图片和相关推荐。详情接口还会使后端新闻浏览量加 1。

### 4.4 查询收藏和浏览历史

收藏页面：`src/views/Favorite.vue`

```text
onMounted()
  -> favoriteStore.getFavoriteListApi()
  -> GET /api/favorite/list?page=1&pageSize=10
  -> favoriteStore.favorites = response.data.data.list
```

历史页面：`src/views/History.vue`

```text
onMounted()
  -> historyStore.getHistoryListApi()
  -> GET /api/history/list
  -> historyStore.history = response.data.data.list
  -> saveHistory()
```

未登录或接口失败时，历史 Store 会尝试从 `localStorage` 加载 `news_history`。收藏 Store 也保留了 `loadFavorites()` 作为本地数据加载方法。

### 4.5 查询用户信息和收藏状态

用户信息：

```text
userStore.getUserInfoDetail()
  -> GET /api/user/info
  -> Header: Authorization: token
  -> userStore.userInfo = response.data.data
```

收藏状态：

```text
favoriteStore.checkFavoriteStatusApi(newsId)
  -> GET /api/favorite/check?newsId=<id>
  -> 返回 isFavorite
```

详情页加载时会检查后端收藏状态，并同步本地 `favorites`，避免本地状态与服务器状态不一致。

## 5. Update：前端修改数据

### 5.1 修改个人简介

页面：`src/views/Profile.vue`

```text
点击“个人简介”
  -> 打开 Dialog
  -> 用户编辑 bio
  -> userStore.updateUserBio(bio)
  -> PUT /api/user/update
  -> Body: { bio }
```

接口成功后，Store 更新：

```js
this.userInfo.bio = bio
```

页面通过计算属性重新显示新的简介。

### 5.2 修改密码

页面收集旧密码、新密码和确认密码，前端先校验：

```text
旧密码不能为空
新密码不能为空
两次新密码必须一致
```

通过校验后调用：

```text
userStore.updatePassword(oldPassword, newPassword)
  -> PUT /api/user/password
  -> Body: { oldPassword, newPassword }
```

密码修改成功后，页面只显示成功提示，不把密码保存到 Pinia 或 `localStorage`。

### 5.3 浏览量和浏览时间的更新

前端没有单独的“修改新闻浏览量”按钮，但打开详情会触发后端更新浏览量；重复打开同一新闻时，后端会更新历史记录的浏览时间。

因此，从前端角度看：

```text
读取详情
  -> 后端自动更新 news.views
  -> 前端接收更新后的详情

记录历史
  -> 后端发现已有记录时更新 view_time
  -> 前端刷新历史列表时读取新的时间
```

## 6. Delete：前端删除数据

### 6.1 删除单条收藏

页面点击收藏项右侧的删除按钮，先弹出确认框：

```text
Favorite.vue:confirmDelete(id)
  -> 用户确认
  -> removeFavorite(id)
  -> favoriteStore.removeFavoriteApi(id)
  -> DELETE /api/favorite/remove?newsId=<id>
```

接口成功后，Store 执行：

```js
this.removeFavorite(id)
  -> favorites 过滤掉指定新闻
  -> saveFavorites()
```

### 6.2 清空收藏

```text
Favorite.vue:onClickClear()
  -> 用户确认
  -> favoriteStore.clearFavoritesApi()
  -> DELETE /api/favorite/clear
  -> 接口成功
  -> clearFavorites()
  -> favorites = []
  -> localStorage 更新为空数组
```

### 6.3 删除单条或全部历史

删除单条：

```text
History.vue:confirmDelete(id)
  -> historyStore.removeHistoryApi(id)
  -> DELETE /api/history/delete/<id>
  -> 成功后 removeHistory(id)
  -> history 过滤指定记录
  -> saveHistory()
```

清空全部：

```text
History.vue:onClickClear()
  -> historyStore.clearHistoryApi()
  -> DELETE /api/history/clear
  -> 成功后 clearHistory()
  -> history = []
  -> localStorage 更新为空数组
```

### 6.4 退出登录

退出登录属于前端状态删除，不是后端数据库删除：

```text
My.vue:handleLogout()
  -> 用户确认
  -> userStore.logout()
  -> userInfo = null
  -> token = ''
  -> isLogin = false
  -> 跳转 /login
```

## 7. 前端状态与页面的对应关系

| Store | 主要状态 | 使用页面 |
| --- | --- | --- |
| `news` | `categories`、`newsList`、`newsDetail`、`loading`、`finished` | `Home.vue`、`NewsDetail.vue` |
| `favorite` | `favorites`、`loading` | `NewsDetail.vue`、`Favorite.vue` |
| `history` | `history` | `NewsDetail.vue`、`History.vue` |
| `user` | `userInfo`、`token`、`isLogin` | `Login.vue`、`Register.vue`、`My.vue`、`Profile.vue` |

前端更新数组或对象时，Vue 会通过 Pinia 的响应式机制自动重新渲染依赖该状态的组件。

## 8. 前端开发新 CRUD 功能的步骤

新增一个业务模块时，可以按以下顺序实现：

1. 在 `src/store/` 中确定状态：列表、详情、当前项、加载状态和错误状态。
2. 编写 Store action：组装请求参数，调用 Axios，判断 `response.data.code`。
3. 成功后更新 Store state；需要离线或未登录回退时，再同步 `localStorage`。
4. 在 `src/views/` 中绑定表单、按钮、列表和空状态。
5. 页面只调用 Store action，不在页面中重复写接口地址和 Token 处理。
6. 对新增、删除、清空等操作增加确认框或成功/失败提示。
7. 对列表查询处理首次加载、刷新、分页追加和无更多数据状态。

## 9. 前端联调注意项

- 登录接口成功后，后续私有接口必须带 `Authorization: userStore.token`。
- 前端只有在 `code === 200` 时更新本地列表，失败响应应保留原状态。
- `pageSize`、`newsId`、`oldPassword` 等请求字段要和后端约定的驼峰字段保持一致。
- 页面展示字段也要统一，例如新闻时间当前存在 `publishTime`、`publish_time`、`publishedTime` 的命名差异。
- 收藏和历史同时存在后端数据与本地缓存时，应明确后端数据的优先级，避免两套列表互相覆盖。
- 当前 `userStore.updateUserBio` 依赖后端返回成功后更新本地简介；后端 `crud/users.py:update_user` 目前存在返回变量写错的问题，联调时需要先修正。
