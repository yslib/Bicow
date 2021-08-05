----
-   应用层向Taichi传递处理图像所需要的参数的时候，可能无法用比较舒服的方式来实现。
    因为taichi在一定程度上相当于静态语言了，无法利用python动态特性。taichi变量需要
    硬编码的全局变量，这样在扩展的时候，只能手写。

-   目前有个问题

```
RuntimeError: [llvm_context.cpp:taichi::lang::TaichiLLVMContext::clone_runtime_module@363] Assertion failure: std::this_thread::get_id() == main_thread_id
```

看来dearpygui的线程不是主线程，设计得改一下了。

改变参数更新逻辑可以在taichi_backend里面做
现在的问题是如何区分事件类型


2021-08-05
dearpygui 的file dialog 有很多Bug。 现在换gui框架已经不太现实了。凑合用吧，之后把文件对话框
可以改成传统的GUI。

而且绘制大图片效率很低，得给管线加上输出缩略图的功能。

ImageWidget 需要继续完善