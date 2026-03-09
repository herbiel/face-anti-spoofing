# Face Anti-Spoofing API 文档

本文档描述了用于人脸活体检测（真假脸识别）的 API 接口。

## 接口地址

- **URL:** `/predict`
- **Method:** `GET`
- **Content-Type:** `application/json`

## 请求参数 (Query Parameters)

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
| :--- | :--- | :---: | :--- | :--- |
| `source` | `string` | **是** | - | 本地图片文件的绝对路径或网络图片的 HTTP/HTTPS URL。 |
| `confidence` | `float` | 否 | `0.5` | 人脸检测的置信度阈值。低于此值的人脸将被忽略。 |

## 响应结构

无论请求业务上是否成功（比如找不到推片或者下载失败），HTTP 状态码都会返回 `200`，真实的业务状态保存在 JSON 响体的 `code` 字段中。

| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `code` | `int` | 业务状态码。`200` 表示检测正常执行完成，`500` 表示发生错误（如图片加载失败等）。 |
| `faces` | `array` | 检测到的人脸列表。如果 `code` 为 500，或者图片中没有检测到人脸，则为空数组 `[]`。 |
| `message`| `string` | 错误信息。当 `code` 为 200 时，该字段为空字符串 `""`；当 `code` 为 500 时，这里会包含具体的错误原因。 |

**`faces` 数组内部对象结构：**

| 字段名 | 类型 | 描述 |
| :--- | :--- | :--- |
| `label` | `string` | 活体检测结果标签。可能的值：`"Real"` (真脸) 或 `"Fake"` (假脸/欺诈攻击)。 |
| `score` | `float` | 检测结果的置信度得分，范围 `[0.0, 1.0]`，值越接近 1 则越确信标签的判断。 |
| `bbox` | `array` | 人脸的边界框坐标 `[x1, y1, x2, y2]`。 |

## 调用示例

### 1. 成功检测 (本地图片)

**请求:**
```bash
curl -X GET "https://facedetect.dodolame.com:8805/predict?source=/path/to/image.jpg"
```

**响应 (`200 OK`):**
```json
{
  "code": 200,
  "faces": [
    {
      "label": "Fake",
      "score": 0.9998348951339722,
      "bbox": [225, 539, 444, 657]
    }
  ],
  "message": ""
}
```

### 2. 成功检测，但未发现人脸

**请求:**
```bash
curl -X GET "https://facedetect.dodolame.com:8805/predict?source=/path/to/landscape.jpg"
```

**响应 (`200 OK`):**
```json
{
  "code": 200,
  "faces": [],
  "message": ""
}
```

### 3. 图片加载失败 (例如路径错误)

**请求:**
```bash
curl -X GET "https://facedetect.dodolame.com:8805/predict?source=bad_path_here"
```

**响应 (`200 OK`):**
```json
{
  "code": 500,
  "faces": [],
  "message": "Failed to load image from local path: bad_path_here"
}
```

## 其他说明

- 默认情况下内部程序监听在 `http://127.0.0.1:8000`，并通过 HAProxy 代理到 `https://facedetect.dodolame.com:8805`。
- 因为服务由 FastAPI 强力驱动，您也可以在浏览器中访问 [https://facedetect.dodolame.com:8805/docs](https://facedetect.dodolame.com:8805/docs) 来查看并测试交互式的 OpenAPI（Swagger）自动生成文档。
