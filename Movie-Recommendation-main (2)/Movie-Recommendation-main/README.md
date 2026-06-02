# 电影推荐系统

> 后端同学写的说明文档，请所有队友仔细阅读

---

## 一、项目结构（每个人把自己的代码放在对应文件夹）

PythonProject/
├── backend/          # 后端代码（后端同学）

├── algorithm/        # 算法代码（算法同学）

├── frontend/         # 前端代码（前端同学）

├── data/             # 数据集（自己下载）

├── scripts/          # 工具脚本

├── README.md         # 说明文档

└── requirements.txt  # 依赖列表（所有人都要装）




---

## 二、环境搭建（每个人都要做，只做一次）

第一步：克隆仓库，命令：
git clone <仓库地址> cd 你的项目目录

第二步：创建虚拟环境
Windows 执行：
python -m venv .venv

.venv\Scripts\activate

第三步：安装依赖
pip install -r requirements.txt

---

## 三、依赖管理（重要）

依赖文件 requirements.txt 内容如下：
fastapi==0.115.6
uvicorn==0.34.0
peewee==3.17.8
pymysql==1.1.1
mysql-connector-python==9.1.0
pydantic==2.10.4
pandas==2.2.3
numpy==2.2.1
scikit-learn==1.6.1

如果你装了新的依赖：
装完立即执行 pip freeze > requirements.txt
然后提交到 Git：
git add requirements.txt
git commit -m "更新依赖"
git push origin <你的分支>

每次拉取代码后，如果 requirements.txt 有变化，执行：
pip install -r requirements.txt

---

## 四、Git 工作流程（大家统一）

分支说明（远程已有）：
- main 分支：稳定代码，最终合并到这里
- backend 分支：后端同学用
- frontend 分支：前端同学用
- algorithm 分支：算法同学用

每个人本地只有一个分支

每天开始工作前（同步 main 的最新代码）：
git pull origin main

开发完后提交：
git add .
git commit -m "写了什么功能"
git push origin <你的分支>
例如后端同学执行：git push origin backend

完成一个大功能后：
1. 去 GitHub 网页发起 Pull Request：你的分支 → main
2. 通知其他人 Review
3. 合并后，其他人执行 git pull origin main 同步

如果出现冲突：
打开冲突文件，找到 <<<<<<< 和 >>>>>>>，手动保留需要的代码，然后执行：
git add .
git commit -m "解决冲突"
git push origin <你的分支>

---

## 五、下载数据集（每个人自己下）

1. 访问 https://grouplens.org/datasets/movielens/100k/
2. 下载 ml-100k.zip
3. 解压到 data/ml-100k/ 文件夹

---

## 六、运行后端服务（后端同学做，其他人不用）

uvicorn backend.app.main:app --reload

然后访问 http://127.0.0.1:8000/docs 查看接口文档

---

## 七、各角色任务清单

后端同学：
- [x] 数据库设计
- [x] 用户注册/登录接口
- [x] 电影列表接口
- [x] 评分接口
- [ ] 推荐接口（等算法模块）
- [ ] Docker 部署

算法同学：
- [ ] 实现 algorithm/user_based.py，提供 recommend(user_id, top_n) 函数
- [ ] 实现 algorithm/item_based.py，提供 recommend(user_ratings, top_n) 函数
- [ ] 冷启动推荐
- [ ] 推荐质量评估（RMSE）

前端同学：
- [ ] Streamlit 界面
- [ ] 调用后端 API
- [ ] 展示推荐结果

PM：
- [ ] 进度跟踪
- [ ] 最终报告
- [ ] PPT
- [ ] 演示视频

---

## 八、常见问题

Q：运行报错 ModuleNotFoundError
A：先执行 pip install -r requirements.txt



Q：git push 报错
A：先 git pull origin main 再 push

---

有问题群里问，不要自己卡太久。