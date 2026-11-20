import test from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {fitStudio} from "../src/studio.js";

test("calibration and impact keep the mount, printed target and strike surface aligned", async t => {
  const context = new Proxy({createLinearGradient: () => ({addColorStop() {}})}, {
    get: (object, key) => object[key] ?? (() => {}),
  });
  globalThis.document = {createElement: () => ({getContext: () => context})};
  globalThis.window = {matchMedia: () => ({matches: false})};
  t.after(() => { delete globalThis.window; delete globalThis.document; });
  const {instrumentPads, strikeZone} = await import("../src/strike-pads.js");
  const scene = new THREE.Scene();
  const bags = fitStudio(scene);
  const kit = instrumentPads(bags);
  const heights = [.02, -.19, .30, .23, -.26];

  function rayHit(face, y, rear = false) {
    scene.updateMatrixWorld(true);
    const origin = face.localToWorld(new THREE.Vector3(.12, y, rear ? -2 : 2));
    const direction = face.localToWorld(new THREE.Vector3(.12, y, 0)).sub(origin).normalize();
    return new THREE.Raycaster(origin, direction).intersectObject(face, false)[0];
  }
  for (const height of [.8, 2]) {
    for (const posture of ["seated", "standing"]) {
      kit.calibrate({height, posture, width: .4}, true);
      scene.updateMatrixWorld(true);
      const [left, right] = bags.map(({face}) => new THREE.Box3().setFromObject(face, true));
      assert.ok(left.max.x < right.min.x);
      for (const {hanger, face} of bags) {
        const rodEnd = hanger.localToWorld(new THREE.Vector3(0, -.335, 0));
        assert.ok(rodEnd.distanceTo(face.parent.getWorldPosition(new THREE.Vector3())) < .00001);
        assert.equal(face.children[0].geometry, face.geometry);
      }
      for (const [index, y] of heights.entries()) {
        const {face} = bags[index % 2];
        assert.equal(strikeZone(rayHit(face, y)), index);
        assert.equal(strikeZone(rayHit(face, y, true)), -1);
      }
    }
  }
  const {face} = bags[0];
  const hit = rayHit(face, heights[0]);
  const before = face.worldToLocal(hit.point.clone()).z;
  const state = {cue: {index: 0}, hold: 0, hover: -1, kind: "go", recall: false, remaining: 0};
  kit.contact(0, "strike", 100, hit);
  kit.paint(205, 16, state);
  const dent = rayHit(face, heights[0]);
  assert.equal(strikeZone(dent), 0);
  assert.ok(face.worldToLocal(dent.point.clone()).z < before - .055);
  kit.paint(700, 16, state);
  assert.ok(Math.abs(face.worldToLocal(rayHit(face, heights[0]).point.clone()).z - before) < .00001);
});
