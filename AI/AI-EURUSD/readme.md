
# Chantier de recherche expérimentale sur la prédiction du cours de l'EUR/USD en utilisant le deep learning.

## Exemple de critères variables pour la recherche expérimentale :

3 couches LSTM

100 et 50 neurones par couche LSTM

Historique de données téléchargées en H1 de 01-06-2022 au 21-04-2023

Nombre de derniers prix pour la prédiction : 100

### Résultats

1 epoch : RMSE moyen = 0.012 (USD) ; 0.011 avec 50 neurones par couche LSTM

2 epoch : RMSE moyen = 0.006 (USD) ; 0.009 avec 50 neurones par couche LSTM

3 epoch : RMSE Moyen = 0.017 (USD) ; 0.007 avec 50 neurones par couche LSTM

4 epoch : RMSE Moyen = 0.007 (USD) ; 0.007 avec 50 neurones par couche LSTM

5 epoch : RMSE Moyen = 0.006 (USD) ; 0.007 avec 50 neurones par couche LSTM

# Configufation technique (lscpu)

Architecture:            x86_64

  CPU op-mode(s):        32-bit, 64-bit
  
  Address sizes:         48 bits physical, 48 bits virtual
  
  Byte Order:            Little Endian
  
CPU(s):                  16

  On-line CPU(s) list:   0-15
  
Vendor ID:               AuthenticAMD

  Model name:            AMD EPYC 7B13
  
    CPU family:          25
    
    Model:               1
    
    Thread(s) per core:  2
    
    Core(s) per socket:  8
    
    Socket(s):           1
    
    Stepping:            0
    
    BogoMIPS:            4899.99
    
    Flags:               fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ht syscall nx mmxext fxsr_opt pdpe1gb rdtscp lm constant_tsc rep_good nopl nonstop_tsc cpuid ex
    
                         td_apicid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 movbe popcnt aes xsave avx f16c rdrand hypervisor lahf_lm cmp_legacy cr8_legacy abm sse4a misalignsse 3dnowprefetch osvw
                         
                          topoext invpcid_single ssbd ibrs ibpb stibp vmmcall fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid rdseed adx smap clflushopt clwb sha_ni xsaveopt xsavec xgetbv1 clzero xsaveerptr arat n
                          
                         pt nrip_save umip vaes vpclmulqdq rdpid fsrm
                         
Virtualization features: 

  Hypervisor vendor:     KVM
  
  Virtualization type:   full
  
Caches (sum of all):     

  L1d:                   256 KiB (8 instances)
  
  L1i:                   256 KiB (8 instances)
  
  L2:                    4 MiB (8 instances)
  
  L3:                    32 MiB (1 instance)
  
NUMA:                    

  NUMA node(s):          1
  
  NUMA node0 CPU(s):     0-15
  
Vulnerabilities:         

  Itlb multihit:         Not affected
  
  L1tf:                  Not affected
  
  Mds:                   Not affected
  
  Meltdown:              Not affected
  
  Mmio stale data:       Not affected
  
  Retbleed:              Not affected
  
  Spec store bypass:     Mitigation; Speculative Store Bypass disabled via prctl and seccomp
  
  Spectre v1:            Mitigation; usercopy/swapgs barriers and __user pointer sanitization
  
  Spectre v2:            Mitigation; Retpolines, IBPB conditional, IBRS_FW, STIBP conditional, RSB filling
  
  Srbds:                 Not affected
  
  Tsx async abort:       Not affected
  
  
