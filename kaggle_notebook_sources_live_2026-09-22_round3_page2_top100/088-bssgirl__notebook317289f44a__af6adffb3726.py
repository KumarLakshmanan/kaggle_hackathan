code = """
import sys

def agent(obs, conf):
    # طباعة الملاحظات في الخطوة الأولى لمعرفة القوام الحقيقي للبيانات
    step = getattr(obs, 'step', 0) if not isinstance(obs, dict) else obs.get('step', 0)
    if step == 0:
        print("=== OBS STRUCTURE ===", file=sys.stderr)
        print(repr(obs), file=sys.stderr)

    # 1. استخراج الأفعال المتاحة بأمان تام
    legal = []
    if hasattr(obs, 'legal_actions'):
        legal = obs.legal_actions
    elif isinstance(obs, dict) and 'legal_actions' in obs:
        legal = obs['legal_actions']

    if not legal:
        return 0

    # 2. مطابقة الأفعال بناءً على أنواعها المختلفة
    harvest_act, water_act, plant_act = None, None, None

    for act in legal:
        act_s = str(act).lower()
        if 'harvest' in act_s or act == 3:
            harvest_act = act
        elif 'water' in act_s or act == 2:
            water_act = act
        elif 'plant' in act_s or act == 1:
            plant_act = act

    # 3. اتخاذ القرار الأولوية
    if harvest_act is not None:
        return harvest_act
    if water_act is not None:
        return water_act
    if plant_act is not None:
        return plant_act

    # إرجاع أول فعل متاح بدلاً من الاستسلام عند عدم التطابق
    return legal[0]
"""

with open("submission.py", "w") as f:
    f.write(code)

print("تم كتابة عميل التشخيص والمطابقة الآمنة بنجاح!")
