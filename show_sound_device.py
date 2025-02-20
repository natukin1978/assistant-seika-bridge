import sounddevice as sd

if __name__ == "__main__":
    """利用可能なオーディオデバイスをリスト表示する"""
    devices = sd.query_devices()
    print(devices)
    while True:
        print("Enter the number and it will print the device name.", end=" ")
        i_str = input()
        if not i_str:
            break
        i = int(i_str)
        device = devices[i]
        hostapi = sd.query_hostapis(device["hostapi"])
        full_name = f'{device["name"]}, {hostapi["name"]}'
        print('"' + full_name + '"')
