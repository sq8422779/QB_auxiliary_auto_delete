# QB_auxiliary_auto_delete

自动删除QB中的种子

### 原理

配置好服务器用户和密码后，会自动连接上QB，然后会获取qb里所有在的任务，获取最后一次上传的时间，加上配置文件中的天数，可以判断当前文件距离要删除还有多久，当最后一次上传的时间加上设置的时间小于当前时间，则进行判断。
判断这个文件同样的文件名和同样的大小，在QB中是否还有除了自身外，还有没有其他的任务正在运行，如有，那只删除任务，不删除文件，如果另外一个任务没有，则删除任务和文件。
### 配置说明
[qBittorrent]
url = http://192.168.1.2:9003 
username = admin
password = admin

[Settings]
days_threshold = 6
//保留做种天数的设定(单位天)
next_process_interval_minutes = 60
//间隔多久扫描一次(单位分钟)
