# -*- coding: utf-8 -*-
import hashlib
from collections import Counter
from itertools import groupby
import functools
import re

class FindSimilarXpath:
    '''
    功能:

    通过对比快速查找网页重要内容的xpath路径。

    通过传入两个或两个以上的网页内容，
    通过相同的xpath以及不同的内容以获取主要内容性质的xpath，
    并将xpath路径经过一定优化后返回。
    
    使用方法:

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
    '''

    def __init__(self,**kw):
        '''
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
        '''
        global etree
        from lxml import etree
        self._ignore_tag          = [] if not kw.get("ignore_tag")          else kw.get("ignore_tag")
        self._ignore_class        = [] if not kw.get("ignore_class")        else kw.get("ignore_class")
        self._ignore_id           = [] if not kw.get("ignore_id")           else kw.get("ignore_id")
        self._ignore_simple_path  = [] if not kw.get("ignore_simple_path")  else kw.get("ignore_simple_path")
    
    def get_all_xpath_by_ele(self,e):
        '''
        #========================================================
        # 通过任意element对象获取该element树里所有xpath路径的函数
        #========================================================
        '''
        v = e.getroottree()
        p = []
        def func(e):
            for i in e:
                # "尾部有tr的去掉tr"
                xp = v.getpath(i)
                rm = re.findall("/br\[\d+\]$|/br$",xp)
                if rm:
                    xp = xp.replace(rm[0],'')
                p.append(xp)
                func(i)
        func(e)
        return p

    
    def keep_common(self,*e,mode="all"):
        '''
        #========================================================
        # 通过多个element对象对各对象所有的xpath找到交集的函数
        #========================================================
        '''
        le = len(e)
        for idx,i in enumerate(e):
            if mode == "all":
                # 获取全部的xpath
                setattr(self,"_v%d"%idx, self.get_all_xpath_by_ele(i))
            if mode == "str":
                # 用string(.)函数对比其字符串进行获取，# 暂时没有任何函数调用到
                setattr(self,"_v%d"%idx, self._get_xpath_by_clsstr(i))
        ls = [getattr(self,"_v%d"%i) for i in range(le)]
        def keep_common_in_2(m1,m2):
            p = []
            for i in m1:
                if i in m2:
                    p.append(i)
            return p
        return functools.reduce(keep_common_in_2,ls)


    def _get_common_key(self,val,key,rke):
        '''
        #========================================================
        # tools. 附属于get_simple_path函数的工具函数
        # 通过xpath路径获取其备用key，如果之后key不唯一可以用这个组装原key进行key唯一化
        '''
        v = re.findall('[^/]+\[\d+\]',val.split(key)[0])
        lke = '_'.join(v)
        if lke:
            k = '_' + lke + rke.replace('/','_')
        else:
            k = rke.replace('/','_')
        return k

    
    def get_simple_path(self,e,xp,el=None):
        '''
        #========================================================
        # 优化路径的函数
        # 通过element和xpath对xpath的路径进行优化
        # el参数为对所有的element获取到的xpath进行去重后转的list
        # el参数如果有的话就可以从后置路径的唯一性考虑优化
        #     例如 /html/body/title
        #     如果 title 在全篇只有一个而且没有id和class属性
        #     那么函数就会输出 //title
        #========================================================
        # 这里注意：
        # el参数若是通过类实例调用detect_by_*这些函数时会默认传入
        # 所以不用担心使用，但是在单独使用该函数时不会传入
        # 没有el参数时基本也无影响，仍然能对id和class进行优先考虑
        #========================================================
        '''
        v = xp.count('/')
        # 优先找路径上的id和class项优化路径
        for i in range(v):
            xpa = xp.rsplit('/',i)[0]
            rke = '/'.join(xp.rsplit('/',i)[1:])
            ele = e.xpath(xpa)[0].attrib
            tag = e.xpath(xpa)[0].tag
            # 去除一些特殊tag 比如script
            if i==0 and tag in self._ignore_tag:
                return None
            if 'id' in ele:
                key = ele["id"]
                if key in self._ignore_id:
                    return None
                rke = '/'+rke if rke else ""
                val = '//%s[@id="%s"]%s'%(xpa.rsplit('/',1)[1],ele["id"],rke)
                return key,val,self._get_common_key(val,key,rke)
            if 'class' in ele:
                key = ele["class"]
                if key in self._ignore_class:
                    return None
                rke = '/'+rke if rke else ""
                val = '//%s[@class="%s"]%s'%(xpa.rsplit('/',1)[1],ele["class"],rke)
                if not key.strip():
                    continue
                return key,val,self._get_common_key(val,key,rke)

        # 从后置路径的唯一性考虑优化
        # 如果没有传入el就直接用路径md5作为key返出，一般输入了el参数这里肯定会返回
        if el is not None:
            for i in range(v):
                xpa = xp.rsplit('/',i)[0]
                rke = '/'.join(xp.rsplit('/',i)[1:])
                v = list(map(lambda i:i.endswith(rke),el)).count(True)
                if v == 1:
                    return rke,'//'+rke,""
        # 这里一般用不上，除非你忘了传入el参数或者单独使用这个函数才可能会使用
        m = hashlib.md5()
        m.update(xp.encode())
        key = m.hexdigest()
        val = xp
        return key,val,""


    
    def _duplicate_removal(self,pack):
        '''
        #========================================================
        # 去除重复Key名
        #========================================================
        '''
        a,b,c = zip(*pack)
        c = []
        for i,j,k in pack:
            if j in self._ignore_simple_path:
                continue
            if a.count(i) == 1:
                c.append([i,j])
            if a.count(i) != 1:
                c.append([i+k,j])
        return c

    def _findall_pack(self,*e):
        '''
        #========================================================
        # 工具函数，用来查找所有的key_val配对的list
        #========================================================
        '''
        assert len(e)>1,"这个比较函数至少需要两个参数"
        el = list(set(functools.reduce(lambda i,j:i+j,[self.get_all_xpath_by_ele(i) for i in e])))
        p = []
        # 全模式获取xpath
        for i in self.keep_common(*e):
            es = [j.xpath(i)[0].text if j.xpath(i)[0].tag not in ['p','span'] else
                  j.xpath(i)[0].xpath("string(.)") for j in e]
            if all(es) and len(Counter(map(lambda i:i.strip(),es)))!=1:
                v = self.get_simple_path(e[0],i,el)
                if v:
                    p.append(v)
        '''
        # 留作扩展思路，目前功能已够这里暂时不许要用到。
        # 用含有class属性且以xpath的string函数获取的字符串对比模式获取xpath
        # 如果出现树状态获取，则会只取匹配到的根，稍微粗糙的模式
        if self._class_string:
            for i in self.keep_common(*e,mode="str"):
                es = [j.xpath(i)[0].xpath("string(.)") if j.xpath(i) else "" for j in e]
                if all(es) and len(Counter(map(lambda i:i.strip(),es)))!=1:
                    v = self.get_simple_path(e[0],i,el)
                    if v:
                        p.append(v)
        '''
        return p

    def _find_table_tag_by_x(self,e,xp):
        '''
        #========================================================
        # 获取父路径直到找到table tag的xpath
        #========================================================
        '''
        lxp = re.findall("(//.*?)/",xp)[0]
        rxp = re.findall("//.*?/(td.*?$)",xp)[0]
        v = e.xpath(lxp)[0]
        # 向上去找table的xpath
        def get_table_xpath(v, p=[]):
            t = v.getparent()
            p.append(t.tag)
            if t is None and "table" not in p:
                print('none table.')
                return
            if t.tag != 'table':
                return get_table_xpath(t, p)
            if t.tag == 'table':
                return t,p
        global tb
        # 向下找th tag来找col的名字
        def get_th_string(tb):
            t = tb.getchildren()
            if not t:
                print('none th.')
                return None
            if t[0].tag != 'th':
                return get_th_string(t[0])
            if t[0].tag == 'th':
                return [i.xpath("string(.)") for i in t]
        tb,vv = get_table_xpath(v)
        if tb is None:
            return
        return '//'+'/'.join(vv[::-1]) + lxp[1:], './'+rxp, get_th_string(tb)


    
    def _create_table(self,e,key_val):
        '''
        #========================================================
        # 生成目标表格dict样式
        #========================================================
        '''
        p = []
        for i,j in key_val:
            x = self._find_table_tag_by_x(e,j)
            if x:
                p.append((i,) + x)
        a,b,c,d = zip(*p)
        idx = 0
        d = {}
        # 在进入该函数时候已经确定了表就是同一张表，所以用下面方法获取rows
        d["rows"] = re.sub('/tr\[\d+\]','/tr',b[0])
        v = {}
        for i,j in groupby(b):
            ls = list(j)
            for aa,bb,cc,dd in p[idx:idx+len(ls)]:
                idnum = re.findall('\[(\d)\]',cc)
                if not idnum:
                    idnum = 1
                else:
                    idnum = int(idnum[0])
                if dd is not None and len(dd) >= idnum:
                    name = dd[idnum-1]
                else:
                    name = cc
                path = cc
                v[name] = path
            idx += len(ls)
        d["table"] = v
        return d

    def _find_table(self,e,fi):
        '''
        #========================================================
        # 判断key里面有没有同时存在tr和td
        # 如果有着尝试以获取表格函数进行处理
        #========================================================
        '''
        if not fi:
            return False #输入为空
        def func(i,y=True):
            a1 = '_tr' in i[0] and '_td' in i[0]
            b1 = '/tr' in i[1] and '/td' in i[1]
            if y:
                return (a1 and b1)
            else:
                return not(a1 and b1)

        yfunc = lambda i:func(i)
        nfunc = lambda i:func(i,False)
        t  = list(filter(yfunc,fi))
        pt = list(filter(nfunc,fi))
        if not t:
            return False #没有表
        tables_name = set()
        for i in t:
            v = re.findall('^(.*?)_tr\[\d+\]',i[0])
            if v:
                tables_name.add(v[0])
        # 考虑到可能会出现多表格的情况，这里作了如下处理
        # 通过名字获取表格的数量以及其表格名字，有相同“key名字”便是相同表格
        tables_name = sorted(list(tables_name),key=lambda i:-len(i))
        tables = []
        for i in tables_name:
            idx_num = []
            key_val = []
            for idx,(x,j) in enumerate(t):
                if x.startswith(i):
                    idx_num.append(idx)
            for idx in idx_num[::-1]:
                key_val.append(t.pop(idx))
            tables.append(self._create_table(e,key_val[::-1]))
        return pt,tables

    def _get_keyval_and_tables(self,*e):
        '''
        #========================================================
        # 获取需要的信息的函数，有两个返回值
        # 1. 第一个dict: key_val配对的dict（如有table会去除table的路径）
        # 2. 第二个list: table表，list里面每个元素是dict
        # 没有则为空
        #========================================================
        '''
        pk = self._findall_pack(*e)
        if not pk:
            print("none match. pls check html.")
            return {},[]
        fi = self._duplicate_removal(pk)
        # 判断table
        v = self._find_table(e[0],fi)
        if v:
            a,b = v
            return dict(a),b
        else:
            fi = list(filter(lambda i:"table" not in i[1],fi))
            return dict(fi),[]

    def _get_xpath_by_clsstr(self,e):
        '''
        #========================================================
        # 存在类名则加入考虑备选
        #========================================================
        '''
        t = ""
        pk = []
        for i in e.getiterator():
            v = e.getroottree()
            if 'class' in i.attrib:
                p = v.getpath(i)
                c = i.xpath('string(.)')
                if c.strip() == t:
                    continue
                if c.strip() in t:
                    continue
                t = c.strip()
                pk.append(p)
        return pk

    def format_print(self,a1,b1):
        """
        #========================================================
        # tools . 测试输出函数
        #========================================================
        """
        print('测试输出：')
        print("[ key_val ]")
        if a1:
            a,b = zip(*a1.items())
            f = '%%%ds'%len(max(a,key=len))
            for i in a1.items():
                print('     ',f%i[0],":",i[1])
        else:
            print('    ',None)
        print("[ tables ]")
        if b1:
            for idx,i in enumerate(b1):
                print("[ table: %d ]" % idx)
                print("    [ rows ]")
                print("    ",i["rows"])
                print("    [ cols ]")
                for j in i["table"].items():
                    print('        ',j)
        else:
            print('    ',None)
        print('========')

    def _simple_requests(self,url):
        global requests
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1)"}
        try:
            r = requests.get(url,headers=headers)
            return r.content
        except:
            raise "url connect error."

    def detect_by_urls(self,*urls):
        '''
        #========================================================
        # 通过多个url来检查，返回两个参数
        # 返回参数同detect_by_eles
        #========================================================
        '''
        es = [etree.HTML(self._simple_requests(i)) for i in urls]
        return self._get_keyval_and_tables(*es)

    def detect_by_filenames(self,*filenames):
        '''
        #========================================================
        # 通过多个filename来检查
        # 返回参数同detect_by_eles
        #========================================================
        '''
        def readfile(filename):
            with open(filename,'rb')as f:
                return f.read()
        es = [etree.HTML(readfile(i)) for i in filenames]
        return self._get_keyval_and_tables(*es)

    def detect_by_eles(self,*eles):
        '''
        #========================================================
        # 通过多个element来检查（lxml.etree），返回两个参数
        # 参数1. {key1:xpath1, key2:xpath2, ...}
        # 考虑多张表时的通用性，所以参数2. 用了下面的结构
        # 参数2. list  => [dict1, dict2, ...]
        #   list.dict1 => {"rows": xpath,
        #                 "table": {key1:xpath1, key2:xpath2, ...}}
        #   list.dict2 => ...
        #========================================================
        '''
        return self._get_keyval_and_tables(*eles)

    def detect_by_strs(self,*strs):
        '''
        #========================================================
        # 通过多个string来检查
        # 返回参数同detect_by_eles
        #========================================================
        '''
        from lxml import etree
        es = [etree.HTML(i) for i in strs]
        return self._get_keyval_and_tables(*es)
            

__all__ = ["FindSimilarXpath"]

