----
-   应用层向Taichi传递处理图像所需要的参数的时候，可能无法用比较舒服的方式来实现。
    因为taichi在一定程度上相当于静态语言了，无法利用python动态特性。taichi变量需要
    硬编码的全局变量，这样在扩展的时候，只能手写。

-   目前有个问题

```
RuntimeError: [llvm_context.cpp:taichi::lang::TaichiLLVMContext::clone_runtime_module@363] Assertion failure: std::this_thread::get_id() == main_thread_id
```

看来dearpygui的线程不是主线程，设计得改一下了。