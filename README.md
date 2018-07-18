pip3 install fxpath; help(fxpath)

功能:
通过对比，快速查找网页重要内容的xpath路径，通过传入两个或两个以上的网页内容，
以相同的xpath以及不同的内容以获取主要内容性质的xpath，并将xpath路径经过一定优化后返回。

使用方法:
```python
eg. 1.
>>>
>>> from lxml import etree
>>> e1 = etree.HTML(html_content)
>>> e2 = etree.HTML(html_content)
>>>
>>> s = FindSimilarXpath()
>>> key_val,tables = s.detect_by_eles(e1,e2)
>>>
eg. 2.
>>>
>>> # 这里只用了一个简单的requests实现
>>> # 如果网页内容不能直接获得，那建议使用detect_by_strs方法。
>>> url1 = 'http://xxx.xxxxx.xxx1'
>>> url2 = 'http://xxx.xxxxx.xxx2'
>>> url3 = 'http://xxx.xxxxx.xxx3'
>>> key_val,tables = s.detect_by_urls(url1,url2,url3)
>>>

>>> s.format_print(key_val,tables) # 通过这个函数格式化输出，以便检查结果
# detect_by_eles, detect_by_urls, detect_by_filenames
# 需要注意的是，detect_by_* 可接受任意数量的参数

FindSimilarXpath:
  **kw:
    ignore_tag
    ignore_class
    ignore_id
    ignore_simple_path

# ignore_* 用在一些需要过滤掉的配置上，默认都为空
# 通过下面格式传 **kw 参数更美观
eg.
>>>
>>> d = {}
>>> d["ignore_tag"]          = ["script",]
>>> d["ignore_class"]        = ["STYLE2"]
>>> d["ignore_id"]           = ["pageNumber"]
>>> d["ignore_simple_path"]  = ["//td[2]/font"]
>>> s = FindSimilarXpath(**kw)
>>>
```
