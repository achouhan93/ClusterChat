import regl from 'regl';
export declare function createQuadBuffer(reglInstance: regl.Regl): {
    buffer: regl.Buffer;
    size: number;
};
export declare function createIndexesBuffer(reglInstance: regl.Regl, textureSize: number): {
    buffer: regl.Buffer;
    size: number;
};
export declare function destroyFramebuffer(fbo?: regl.Framebuffer2D): void;
export declare function destroyBuffer(fbo?: regl.Buffer): void;
