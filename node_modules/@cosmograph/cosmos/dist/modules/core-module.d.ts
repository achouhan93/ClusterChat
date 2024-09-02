import regl from 'regl';
import { GraphConfigInterface } from "../config";
import { GraphData } from "./GraphData";
import { Points } from "./Points";
import { Store } from "./Store";
import { CosmosInputNode, CosmosInputLink } from "../types";
export declare class CoreModule<N extends CosmosInputNode, L extends CosmosInputLink> {
    readonly reglInstance: regl.Regl;
    readonly config: GraphConfigInterface<N, L>;
    readonly store: Store<N>;
    readonly data: GraphData<N, L>;
    readonly points: Points<N, L> | undefined;
    constructor(reglInstance: regl.Regl, config: GraphConfigInterface<N, L>, store: Store<N>, data: GraphData<N, L>, points?: Points<N, L>);
}
