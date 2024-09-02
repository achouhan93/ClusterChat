import regl from 'regl';
import { CoreModule } from "../core-module";
import { CosmosInputNode, CosmosInputLink } from "../../types";
export declare enum LinkDirection {
    OUTGOING = "outgoing",
    INCOMING = "incoming"
}
export declare class ForceLink<N extends CosmosInputNode, L extends CosmosInputLink> extends CoreModule<N, L> {
    linkFirstIndicesAndAmountFbo: regl.Framebuffer2D | undefined;
    indicesFbo: regl.Framebuffer2D | undefined;
    biasAndStrengthFbo: regl.Framebuffer2D | undefined;
    randomDistanceFbo: regl.Framebuffer2D | undefined;
    linkFirstIndicesAndAmount: Float32Array;
    indices: Float32Array;
    maxPointDegree: number;
    private runCommand;
    create(direction: LinkDirection): void;
    initPrograms(): void;
    run(): void;
    destroy(): void;
}
