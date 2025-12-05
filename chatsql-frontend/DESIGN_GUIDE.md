# ChatSQL Frontend Design Guide

## 设计哲学：原生 macOS 窗口 & 专业 SaaS

UI 必须感觉像一个原生 macOS 应用程序浮动在桌面上，而不是传统网站。优先考虑 "Squircle" 形状、极简主义、清晰度和 "Apple Human Interface" 美学。

---

## 1. 全局布局结构（"窗口"隐喻）

### 桌面背景
- **根容器**：`h-screen w-screen bg-[#F5F5F7]`（学生模式）或 `bg-[#F0F2F5]`（管理员模式）
- **布局**：使用 flexbox 居中主内容：`flex items-center justify-center`

### 应用窗口
主内容是一个大型浮动卡片：

```tsx
<div className="w-full h-full max-w-[1920px] bg-white rounded-3xl shadow-[0_20px_60px_-12px_rgba(0,0,0,0.12)] border border-gray-200 overflow-hidden flex relative">
  {/* 所有侧边栏和内容都在这个圆角容器内 */}
</div>
```

**行为**：它充当 "OS 窗口"。所有侧边栏和内容都存在于这个圆角容器*内部*。

---

## 2. 导航和侧边栏

### 可折叠侧边栏
侧边栏（左侧菜单/问题列表，右侧 AI）必须可折叠，带有平滑过渡：
- `transition-all duration-300`
- 使用 `ease-[cubic-bezier(0.25,0.1,0.25,1)]` 实现 Apple 风格的缓动

### 交通灯控制
侧边栏左上角必须包含三个点（红、黄、绿），模仿 macOS 窗口控制，但映射到应用逻辑：

- 🔴 **红色**：关闭侧边栏
- 🟡 **黄色**：切换/隐藏次要面板（例如 AI Chat）
- 🟢 **绿色**：切换浏览器全屏

**实现示例**：
```tsx
<div className="flex items-center gap-2">
  <button 
    onClick={() => setIsSidebarOpen(false)} 
    className="w-3 h-3 rounded-full bg-[#FF5F57] hover:bg-[#FF5F57]/80 border border-[#E05E58] shadow-sm transition-colors" 
    title="Close Sidebar" 
  />
  <button 
    onClick={() => setIsAIChatOpen(!isAIChatOpen)} 
    className="w-3 h-3 rounded-full bg-[#FEBC2E] hover:bg-[#FEBC2E]/80 border border-[#DFA023] shadow-sm transition-colors" 
    title="Toggle AI Chat" 
  />
  <button 
    onClick={toggleFullscreen} 
    className="w-3 h-3 rounded-full bg-[#28C840] hover:bg-[#28C840]/80 border border-[#23AD37] shadow-sm transition-colors" 
    title="Toggle Fullscreen" 
  />
</div>
```

### 侧边栏样式
- 背景：`bg-[#FAFAFA]` 或 `bg-[#F8F9FA]` 以区别于白色主内容
- 分隔：`border-r border-gray-100`（左侧）或 `border-l border-gray-100`（右侧）

---

## 3. 组件样式规则（严格）

### 按钮

#### 主要按钮
- **形状**：`rounded-full`（胶囊形状）或 `rounded-xl`
- **禁止**：永远不要使用尖锐的角或小的 `rounded-md`
- **交互**：始终包含 `active:scale-95` 和 `transition-all` 以获得触觉反馈

**示例**：
```tsx
<button className="px-6 py-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 active:scale-95 transition-all shadow-md">
  Submit
</button>
```

#### 仅图标按钮
- **形状**：圆形（`rounded-full`）
- **悬停**：通常带有浅灰色悬停效果（`hover:bg-gray-100`）
- **尺寸**：通常 `w-9 h-9` 或 `w-8 h-8`

**示例**：
```tsx
<button className="w-9 h-9 flex items-center justify-center rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
  <svg className="w-4 h-4">...</svg>
</button>
```

### 输入框

- **形状**：`rounded-xl` 或 `rounded-full`
- **样式**：最小边框（`border-gray-200`），聚焦环（`focus:ring-2 focus:ring-blue-500/10`）
- **背景**：`bg-white` 或 `bg-gray-50`（聚焦时变为白色）

**示例**：
```tsx
<input 
  className="w-full px-5 py-3 bg-white border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 focus:bg-white transition-all shadow-sm"
  placeholder="Enter text..."
/>
```

### 卡片/容器

- **内面板**：使用 `rounded-2xl` 或 `rounded-3xl`（如 ResultPanel 或 Dashboard Cards）
- **空状态**：应该包含在圆角边框框中，而不仅仅是浮动文本

**示例**：
```tsx
<div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
  {/* 内容 */}
</div>
```

### 排版

#### 通用文本
- **字体**：系统无衬线（`font-sans`）
- **默认**：Tailwind 配置中已设置为 Apple 系统字体栈

#### 代码
- **强制使用**：Apple 风格等宽字体
- **字体族**：`font-family: "SF Mono", "Menlo", "Monaco", "Courier New", monospace`
- **Tailwind 类**：`font-mono`

**Monaco Editor 配置**：
```tsx
options={{
  fontFamily: '"SF Mono", "Menlo", "Monaco", "Courier New", monospace,
  fontSize: 13,
  lineHeight: 24,
}}
```

#### 标题
- **样式**：粗体，高对比度（`text-gray-900`）
- **字距**：通常使用 `tracking-tight`
- **大小**：使用 `text-xl`、`text-2xl` 等

---

## 4. 颜色调色板

### 学生模式
- **强调色**：**蓝色**（`bg-blue-600`、`text-blue-600`）
- **背景**：清晰的白色

### 教师/管理员模式
- **强调色**：**SaaS 灰色/黑色**（`bg-gray-900`、`text-gray-900`）或**紫色**（`text-purple-600`）
- **背景**：稍微温暖的灰色（`#F9FAFB`）

### 状态颜色

- **成功**：翠绿/绿色（`text-green-700 bg-green-50`）
- **错误**：红色（`text-red-700 bg-red-50`）
- **警告**：黄色/琥珀色（`text-yellow-700 bg-yellow-50`）

---

## 5. 特定组件行为

### 分割视图
使用 `react-split`。拖拽手柄（gutter）必须有一个大的不可见点击区域（通过 `z-index` 和伪元素），但显示为 1px 细线。

**CSS 配置**（已在 `index.css` 中）：
```css
.gutter {
  background-color: transparent;
  position: relative;
  z-index: 9999 !important;
}

.gutter:hover::before,
.gutter:active::before {
  background-color: #3B82F6; /* Apple Blue */
}
```

### 模态框
- **居中**：`flex items-center justify-center`
- **背景模糊**：`backdrop-blur-sm`
- **容器**：`rounded-3xl`、`shadow-2xl`
- **背景覆盖**：`bg-black/20` 或 `bg-black/10`

**示例**：
```tsx
<div className="fixed inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm z-50">
  <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-lg w-full mx-4">
    {/* 内容 */}
  </div>
</div>
```

---

## 6. 滚动条样式

使用自定义滚动条（已在 `index.css` 中配置）：
- **宽度**：6px
- **轨道**：透明
- **滑块**：`bg-gray-300/50`，悬停时 `bg-gray-400/80`
- **形状**：`rounded-full`

**Tailwind 类**：`custom-scrollbar`

---

## 7. 动画和过渡

### 标准过渡
- **持续时间**：`duration-300`（300ms）
- **缓动**：`ease-[cubic-bezier(0.25,0.1,0.25,1)]`（Apple 风格）

### 交互反馈
- **按钮按下**：`active:scale-95`
- **悬停缩放**：`hover:scale-105`（可选，用于主要操作）

---

## 8. 间距和尺寸

### 标准间距
- **容器内边距**：`p-4`、`p-6`、`p-8`
- **元素间距**：`gap-2`、`gap-3`、`gap-4`

### 标准高度
- **工具栏/标题栏**：`h-14`（56px）
- **侧边栏宽度**：`w-[280px]` 或 `w-[320px]`（打开时）

---

## 9. 检查清单

在创建或修改组件时，请确保：

- [ ] 根容器使用正确的背景色（`#F5F5F7` 或 `#F0F2F5`）
- [ ] 应用窗口使用 `rounded-3xl` 和正确的阴影
- [ ] 所有按钮使用 `rounded-full` 或 `rounded-xl`
- [ ] 输入框使用 `rounded-xl` 或 `rounded-full`
- [ ] 代码使用 SF Mono 字体族
- [ ] 侧边栏包含交通灯控制
- [ ] 所有交互包含 `transition-all` 和 `active:scale-95`
- [ ] 颜色符合模式（学生=蓝色，管理员=灰色/紫色）
- [ ] 空状态包含在圆角容器中
- [ ] 滚动条使用 `custom-scrollbar` 类

---

## 10. 示例组件模板

### 标准按钮
```tsx
<button className="px-6 py-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 active:scale-95 transition-all shadow-md">
  Action
</button>
```

### 标准输入框
```tsx
<input 
  className="w-full px-5 py-3 bg-white border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all"
  placeholder="Enter text..."
/>
```

### 标准卡片
```tsx
<div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
  {/* 内容 */}
</div>
```

---

**最后更新**：2024-12-04
**维护者**：ChatSQL Frontend Team

