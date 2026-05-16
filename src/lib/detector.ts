import * as cocoSsd from '@tensorflow-models/coco-ssd';
import '@tensorflow/tfjs';
import type { DetectedObject } from './api.types';

let modelInstance: cocoSsd.ObjectDetection | null = null;
let loadingPromise: Promise<cocoSsd.ObjectDetection> | null = null;

export async function loadModel(): Promise<cocoSsd.ObjectDetection> {
  if (modelInstance) return modelInstance;
  if (loadingPromise) return loadingPromise;

  loadingPromise = cocoSsd.load({ base: 'lite_mobilenet_v2' }).then((m) => {
    modelInstance = m;
    return m;
  });

  return loadingPromise;
}

export async function detectObjects(
  source: HTMLImageElement | HTMLVideoElement | HTMLCanvasElement,
  confidenceThreshold: number
): Promise<DetectedObject[]> {
  const model = await loadModel();
  const predictions = await model.detect(source);

  return predictions
    .filter((p) => p.score >= confidenceThreshold)
    .map((p, idx) => ({
      label: p.class,
      confidence: p.score,
      bbox_x1: p.bbox[0],
      bbox_y1: p.bbox[1],
      bbox_x2: p.bbox[0] + p.bbox[2],
      bbox_y2: p.bbox[1] + p.bbox[3],
      class_id: idx,
    })) as DetectedObject[];
}

export function drawDetections(
  canvas: HTMLCanvasElement,
  detections: DetectedObject[],
  sourceWidth: number,
  sourceHeight: number
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const scaleX = canvas.width / sourceWidth;
  const scaleY = canvas.height / sourceHeight;

  for (const det of detections) {
    const x = det.bbox_x1;
    const y = det.bbox_y1;
    const w = det.bbox_x2 - det.bbox_x1;
    const h = det.bbox_y2 - det.bbox_y1;
    
    const sx = x * scaleX;
    const sy = y * scaleY;
    const sw = w * scaleX;
    const sh = h * scaleY;

    const hue = stringToHue(det.label);
    const color = `hsl(${hue}, 85%, 55%)`;
    const bgColor = `hsla(${hue}, 85%, 55%, 0.15)`;

    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.strokeRect(sx, sy, sw, sh);

    ctx.fillStyle = bgColor;
    ctx.fillRect(sx, sy, sw, sh);

    const label = `${det.label} ${(det.confidence * 100).toFixed(0)}%`;
    ctx.font = 'bold 13px Inter, sans-serif';
    const textWidth = ctx.measureText(label).width;
    const tagH = 22;
    const tagY = sy > tagH ? sy - tagH : sy + sh;

    ctx.fillStyle = color;
    ctx.fillRect(sx - 1, tagY, textWidth + 10, tagH);

    ctx.fillStyle = '#ffffff';
    ctx.fillText(label, sx + 4, tagY + 15);
  }
}

function stringToHue(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return Math.abs(hash) % 360;
}

export const COCO_CLASSES = [
  'person','bicycle','car','motorcycle','airplane','bus','train','truck',
  'boat','traffic light','fire hydrant','stop sign','parking meter','bench',
  'bird','cat','dog','horse','sheep','cow','elephant','bear','zebra','giraffe',
  'backpack','umbrella','handbag','tie','suitcase','frisbee','skis','snowboard',
  'sports ball','kite','baseball bat','baseball glove','skateboard','surfboard',
  'tennis racket','bottle','wine glass','cup','fork','knife','spoon','bowl',
  'banana','apple','sandwich','orange','broccoli','carrot','hot dog','pizza',
  'donut','cake','chair','couch','potted plant','bed','dining table','toilet',
  'tv','laptop','mouse','remote','keyboard','cell phone','microwave','oven',
  'toaster','sink','refrigerator','book','clock','vase','scissors','teddy bear',
  'hair drier','toothbrush',
];
