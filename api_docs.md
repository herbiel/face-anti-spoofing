# Face Anti-Spoofing API 文档

本文档描述了用于人脸活体检测（真假脸识别）的 API 接口。

## 接口地址

- **URL:** `/predict`
- **Method:** `POST`
- **Content-Type:** `application/json`

## 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :---: | :--- | :--- |
| `sources` | `array of strings` | **是** | - | 包含一个或多个本地图片文件绝对路径，或网络 HTTP/HTTPS URL 的列表。 |
| `confidence` | `float` | 否 | `0.5` | 人脸检测的置信度阈值。低于此值的人脸将被忽略。 |

## 响应结构

无论请求业务上是否成功（比如找不到推片或者下载失败），HTTP 状态码都会返回 `200`，真实的业务状态保存在 JSON 响体的 `code` 字段中。

| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `code` | `int` | 顶层状态码。`200` 表示整个请求成功被服务器处理（即便某张图片加载失败，只要服务没崩溃，这仍是 200），`500` 表示发生系统级致命报错。 |
| `results` | `array` | 每张图片的独立检测结果列表。 |
| `message`| `string` | 顶层错误信息。 |

**`results` 数组内部对象结构 (一张图片对应一个结果)：**

| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `source` | `string` | 该结果对应传入的图片路径或 URL。 |
| `faces` | `array` | 检测到的人脸列表。如果 `error` 不为空，或者图片中没有检测到人脸，则为空数组 `[]`。 |
| `error` | `string` | 单张图片的错误信息。成功加载和检测时为空字符串 `""`；抛错时（如加载失败）会包含具体原因，且不影响同批次其他图片的检测。 |

**`faces` 数组内部对象结构：**

| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `label` | `string` | 活体检测结果标签。可能的值：`"Real"` (真脸) 或 `"Fake"` (假脸/欺诈攻击)。 |
| `score` | `float` | 检测结果的置信度得分，范围 `[0.0, 1.0]`，值越接近 1 则越确信标签的判断。 |
| `bbox` | `array` | 人脸的边界框坐标 `[x1, y1, x2, y2]`。 |

## 调用示例

### 1. 成功检测多张图片

**请求:**
```bash
curl -X POST "https://facedetect.dodolame.com:8805/predict" \
     -H "Content-Type: application/json" \
     -d '{
           "sources": [
             "/path/to/image.jpg",
             "https://raw.githubusercontent.com/yakhyo/face-anti-spoofing/main/assets/result_T1.jpg"
           ],
           "confidence": 0.5
         }'
```

**响应 (`200 OK`):**
```json
{
  "code": 200,
  "results": [
    {
      "source": "/path/to/image.jpg",
      "faces": [
        {
          "label": "Fake",
          "score": 0.9998348951339722,
          "bbox": [225, 539, 444, 657]
        }
      ],
      "error": ""
    },
    {
      "source": "https://raw.githubusercontent.com/yakhyo/face-anti-spoofing/main/assets/result_T1.jpg",
      "faces": [
        {
          "label": "Real",
          "score": 0.9999817609786987,
          "bbox": [120, 96, 171, 254]
        }
      ],
      "error": ""
    }
  ],
  "message": ""
}
```

### 2. 部分图片加载失败 (高鲁棒性容错机制)

如果数组中的某一张图片路径错误或是损坏，API 不会整体崩溃报错，而是像下面这样，仅仅单独在对应的结果项中返回非空的 `error` 字段，同批次正常的图片将照旧出结果：

**请求:**
```bash
curl -X POST "https://facedetect.dodolame.com:8805/predict" \
     -H "Content-Type: application/json" \
     -d '{"sources": ["/path/to/landscape.jpg", "bad_path_here"]}'
```

**响应 (`200 OK`):**
```json
{
  "code": 200,
  "results": [
    {
      "source": "/path/to/landscape.jpg",
      "faces": [],
      "error": ""
    },
    {
      "source": "bad_path_here",
      "faces": [],
      "error": "Failed to load image from local path: bad_path_here"
    }
  ],
  "message": ""
}
```

## 其他说明

- 默认情况下内部程序监听在 `http://127.0.0.1:8000`，并通过 HAProxy 代理到 `https://facedetect.dodolame.com:8805`。
- 因为服务由 FastAPI 强力驱动，您也可以在浏览器中访问 [https://facedetect.dodolame.com:8805/docs](https://facedetect.dodolame.com:8805/docs) 来查看并测试交互式的 OpenAPI（Swagger）自动生成文档。
