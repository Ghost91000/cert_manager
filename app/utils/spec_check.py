from datetime import datetime


def compare(old_pc, new_pc):
    history = []
    if new_pc["motherboard"] != old_pc["motherboard"]:
        history.append({"date": datetime.now().strftime('%d-%m-%Y %H:%M:%S'), "old": old_pc["motherboard"], "new": new_pc["motherboard"]})
    if new_pc["cpu"] != old_pc["cpu"]:
        history.append({"date": datetime.now().strftime('%d-%m-%Y %H:%M:%S'), "old": old_pc["cpu"], "new": new_pc["cpu"]})
    if new_pc["gpu"] != old_pc["gpu"]:
        history.append({"date": datetime.now().strftime('%d-%m-%Y %H:%M:%S'), "old": old_pc["gpu"], "new": new_pc["gpu"]})
    if new_pc["ram"] != old_pc["ram"]:
        history.append({"date": datetime.now().strftime('%d-%m-%Y %H:%M:%S'), "old": old_pc["ram"], "new": new_pc["ram"]})
    if new_pc["storage"] != old_pc["storage"]:
        history.append({"date": datetime.now().strftime('%d-%m-%Y %H:%M:%S'), "old": old_pc["storage"], "new": new_pc["storage"]})
    return history