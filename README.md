# pyweb
a simple game publish tool framework that use tornado and websocket

snapshoot

![](./snapshoot/pub.gif)

##Step 0 初始化
```
{node}/server_list/s1   {"create_time":x,"server_name":x,"server_id":x,"versions":{}}
...
{node}/server_list/sN   {"create_time":x,"server_name":x,"server_id":x,"versions":{}}
```

##Step 1 打包
```
{node}/to_zip_notice/v1  {"create_time":x,"pub_id":x,"pub_node_id":x,"config_version":x,"game_version":x}
{node}/to_zip_result/v1  {"create_time":x,"status":"ok"}
```

##Step 2 同步
```
{node}/to_syc_notice/v1    {"create_time":x,"pub_id":x,"pub_node_id":x}
{node}/to_syc_result/v1/s1 {"create_time":x,"status":"ok"}
...
{node}/to_syc_result/v1/sN {"create_time":x,"status":"ok"}
{node}/to_syc_result/v1    {"create_time":x,"status":"ok"} 
```

##Step 3 发布
```
{node}/to_pub_notice/v1    {"create_time":x,"pub_id":x,"pub_node_id":x, "servers":[x,x]}
{node}/to_pub_result/v1/s1 {"create_time":x,"status":"ok"}
...
{node}/to_pub_result/v1/sN {"create_time":x,"status":"ok"}
{node}/to_pub_result/v1    {"create_time":x,"status":"ok"}
```

##Step 4 回滚
```
{node}/to_rol_notice/v1    {"create_time":x,"pub_id":x,"pub_node_id":x, "servers":[x,x]}
{node}/to_rol_result/v1/s1 {"create_time":x,"status":"ok"}
...
{node}/to_rol_result/v1/sN {"create_time":x,"status":"ok"}
{node}/to_rol_result/v1    {"create_time":x,"status":"ok"}
```


