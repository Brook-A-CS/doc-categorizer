import layoutparser as lp
import cv2
from matplotlib import pyplot as plt

print(dir(lp))

# # 1. Load your document page (from a PDF page or scanned doc)
# image_path = "unique1.jpg"  # change this to your image
# image = cv2.imread(image_path)

# # 2. Load a pre-trained model (Detectron2-based)
# # You can choose: PubLayNet model for text/tables/figures, etc.
# model = lp.Detectron2LayoutModel(
#     config_path="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config", 
#     extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5], 
#     label_map={0: "text", 1: "title", 2: "list", 3: "table", 4: "figure"}
# )

# # 3. Detect the layout
# layout = model.detect(image)

# # 4. Visualize
# color_map = {
#     "text": "red",
#     "title": "blue",
#     "list": "green",
#     "table": "purple",
#     "figure": "orange"
# }
# viz = lp.draw_box(image, layout, color_map=color_map, box_width=3)

# # 5. Display
# plt.figure(figsize=(12, 12))
# plt.imshow(cv2.cvtColor(viz, cv2.COLOR_BGR2RGB))
# plt.axis("off")
# plt.show()