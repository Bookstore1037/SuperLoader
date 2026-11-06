import hashlib,urllib.request,pathlib
url='https://cdn.modrinth.com/data/AANobbMI/versions/uMOpc5uV/sodium-neoforge-0.8.13%2Bmc1.21.1.jar'
dest=pathlib.Path(r'D:\SLData\instances\1.21.1\mods\sodium-neoforge-0.8.13+mc1.21.1.jar')
req=urllib.request.Request(url,headers={'User-Agent':'SuperLoader/1.0'})
data=urllib.request.urlopen(req,timeout=120).read()
dest.write_bytes(data)
print('bytes',len(data))
print('sha1',hashlib.sha1(data).hexdigest())
