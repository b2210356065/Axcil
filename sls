Şimdi prompt engineering stategies i son iş akış planına göre güncelle. Burada stratejilerimiz çok ama çok önemli ondan dolayı mevcut iş akışımıza uygun olcak prompt mühendisliğini uygulamamız lazım. İnternetten araştırma yaparak prompt 
stratejilerimizi geliştirmeni istiyorum. Bunun dışında iş akışımızda bulunan bazı kısımlarda olmazsa olmaz diye düşündüğüm bazı prompt stratejileri var onları mümkün olduğunca araştır ve iyileştir. 

Olmazsa olmaz prompt stratejileri:

iş tanımı zenginleştirilirken kullanıcının verdiği iş tanımı kullanıcı gözünden düşünülmeli akıcı ve tutarlı hale getirilmeli iş tanımına ait örnek senaryolar iş tanımı içerisinden referanslanıp iş tanımının en aşağısında bulunmalı iş tanımının hem  
insan hemde yapay zeka tarafından doğru anlaşılması için doğru bir yapıda sunulmalıdır.

yapay zeka tarafından üretilen zenginleştirilmiş iş tanımı beğenilmezse kullanıcı iş tanımını yenile diyebilir bu durumda hatalı olan durumlar tarzı bir alanda kullanıcının iş tanımını neden beğenmediği kullanıcı tarafından yazılabilir. Yapay zekaya 
 yeni bir zenginleştirilmiş iş tanımı oluşturturken kullanıcının yazdığı ilk iş tanımı verilir yapay zeka cevap içerisinde kullanıcının iş tanımını anlamaya çalışır. Sonrasında zenginleştirilmiş ancak başarılı olamamış iş tanımı örneği kullanıcının  
neden beğenmediği bilgisiyle verilir yapay zeka iş tanımını ve kullanıcının ne demek istediğini düşünür ve yeni bir iş tanımı oluşturur. Bu iş tanımı oluşturma üstteki maddedeki ilkeleri barındırmak zorundadır. Aynı zamanda şöyle bir not geçmek      
istiyorum. Zenginleştirilmiş iş tanımı kullanıcı tarafından birden fazla beğenilmeyebilir. Kullanıcı her yeni zenginleştirilmiş iş tanımı istediğinde beğenmediği kısımlar ve önceki iş tanımları database de depolanır. Böylece beğenilmemiş iş tanımı   
yapay zekaya verileceği zaman beğenilmemiş bütün hatalı denemeleri aklında tutar böylece geçmişte tekrarladığı hatayı tekrarlamazken aynı zamanda kullanıcının beğenmediği kısımlar üzerinden daha iyi bir şekilde iş tanımı üzerinden algı 
geliştirebilir. Tabi burada beğenmeme durumu üzerinde durduk ancak kullanıcı öneride verebilir o yüzden beğenmeme kısımlarını eksikler ve öneriler başlığı altında değerlendirmende fayda var.

İş tanımı kullanıcı tarafından beğenildiği durumda o iş tanımına ait bir algoritma yazacağız bildiğin üzere. Bu algoritma yazılırken yapay zeka iş tanımını ve verilmiş örnekleri okur bu iş tanımını tam anlamıyla anlamaya çalışır. Kendi iş tanımına   
göre iş tanımını kapsayan gelişmiş senaryolar tanımlar. Bu senaryo sayısı çok abartılı olmasın iş tanımı içerisindeki her madde için 3 5 senaryo tanımlaması yeterli. Bu senaryoların iş tanımına göre çözümünün nasıl olması gerektiğini düşünür         
çözümleri ve arkasındaki mantığı not eder kafasında. İş tanımının mantığı örnek senaryolar ile anlaşıldıktan sonra yapay zeka kendisine verilen sandbox sınırlamalarına göre bu senaryoların ve iş mantığının altında yatan temel mantığı gözeterek       
gerekli fonksiyonu(ları) yazar. Fonksiyonun(ların) yapay zekanın hazırladığı karmaşık senaryoları doğru bir şekilde işlediğine emin olduktan sonra basit 10 farklı senaryo ile de test eder eğer fonksiyon tamamen başarılıysa o zaman yapay zeka o       
fonksiyonu bizim response içerisinden ayırt edeceğimiz şekilde istediğimiz format içine koyup tekrar yazar. Eğer fonksiyon bahsedildiği gibi başarılı olmadıysa yapay zeka nerede sorun olduğunu tespit eder gerekli değişiklikleri düşünür bu 
değişiklikleri uygular yeni fonksiyon(lar) üzerinden senaryolar ilk başta olduğu gibi test edilir. Eğer test geçmiyorsa aynı aşama tekrarlanır (burada tekrar sayısı 3 tekrar olacak eğer yine başaramazsa yapay zeka detaylı bir sorun öneri raporunu    
başarısızlık durumu için tasarladığımız bir json formatı içerisinde raporlar bu rapor saklanır kullanıcı eğer yine iş mantığı oluşturmak isterse o zaman bu rapor prompt içerisinde verilir ve aynı prosedür yapay zekanın geçmişten ders alacağı şekilde 
 tekrardan uygulanır). Eğer test geçiyorsa testten geçen fonksiyon başarı için tasarladığımız json formatı içine EKSİKSİZ BİR ŞEKİLDE yeniden yazılır bu sayede response içerisinden iş mantığını içeren kodu çıkarıp db ye koyarız.

Eğer yapay zeka başarılı olduğunu düşündüğü bir iş mantığı kodu çıkardıysa ancak kullanıcı bu kodun doğru çalışmadığını gördüyse yeni iş mantığı oluştur diyerek eksiklik ve önerilerini dile getirebilir bu verilen bilgilerde algoritma oluşturma       
promptunda uygun bir alana yerleştirilir böylece daha iyi bir iş mantığı oluşturulabilir.



yukarıdaki prompt stratejileri COT kullanarak yapay zekanın performansını arttırmak üzerine. Ancak COT durumları çok uzarsa o zaman yapay zeka hata yapmaya meyilli olacaktır dolayısıyla bu isteklerimin prompt içerisinde yapay zekanın token 
kalabalığı yapmadan verimli bir şekilde gerçekleştirilmesi gerekiyor. Üstelik modern prompt engineering araştırmalarıyla benim yazdığım prompt stratejilerini iyileştirebilirsin. Gerekli araştırmaları yap bilgileri topla en iyi prompt stratejisini    
sana verdiğim önerilerle düşün ve yeni prompt stratejilerini sentezle. Sentezlediğin farklı promptların stratejilerinide promp_engineering_strategies.md içerisine kaydet. L99.