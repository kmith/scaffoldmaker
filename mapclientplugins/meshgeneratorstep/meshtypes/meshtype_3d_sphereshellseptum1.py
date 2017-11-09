"""
Generates a 3-D 'sphere shell septum' mesh crossing from one side of a sphere
shell to the other, including elements for the outside, suitable for joining
two halves of a sphere shell.
It is the middle line in (|).
The number of elements up the sphere and across the septum can be varied.
Only one element throught the wall is currently implemented.
"""

import math
from opencmiss.zinc.element import Element, Elementbasis, Elementfieldtemplate
from opencmiss.zinc.field import Field
from opencmiss.zinc.node import Node

def interpolateCubicHermite(v1, d1, v2, d2, xi):
    """
    Return cubic Hermite interpolated value of tuples v1, d1 (end 1) to v2, d2 (end 2) for xi in [0,1]
    :return: tuple containing result
    """
    xi2 = xi*xi
    xi3 = xi2*xi
    f1 = 1.0 - 3.0*xi2 + 2.0*xi3
    f2 = xi - 2.0*xi2 + xi3
    f3 = 3.0*xi2 - 2.0*xi3
    f4 = -xi2 + xi3
    result = []
    for i in range(len(v1)):
        result.append(f1*v1[i] + f2*d1[i] + f3*v2[i] + f4*d2[i])
    return tuple(result)

def interpolateCubicHermiteDerivative(v1, d1, v2, d2, xi):
    """
    Return cubic Hermite interpolated derivatives of tuples v1, d1 (end 1) to v2, d2 (end 2) for xi in [0,1]
    :return: tuple containing result
    """
    xi2 = xi*xi
    f1 = -6.0*xi + 6.0*xi2
    f2 = 1.0 - 4.0*xi + 3.0*xi2
    f3 = 6.0*xi - 6.0*xi2
    f4 = -2.0*xi + 3.0*xi2
    result = []
    for i in range(len(v1)):
        result.append(f1*v1[i] + f2*d1[i] + f3*v2[i] + f4*d2[i])
    return tuple(result)

class MeshType_3d_sphereshellseptum1(object):
    '''
    classdocs
    '''
    @staticmethod
    def getName():
        return '3D Sphere Shell Septum 1'

    @staticmethod
    def getDefaultOptions():
        return {
            'Number of elements up' : 4,
            'Number of elements across' : 2,
            'Wall thickness left' : 0.25,
            'Wall thickness right' : 0.25,
            'Apex scale factor identifier offset' : 10000,
            'Use cross derivatives' : False
        }

    @staticmethod
    def getOrderedOptionNames():
        return [
            'Number of elements up',
            'Number of elements across',
            'Wall thickness left',
            'Wall thickness right',
            'Apex scale factor identifier offset',
            'Use cross derivatives'
        ]

    @staticmethod
    def checkOptions(options):
        if (options['Number of elements up'] < 2) :
            options['Number of elements up'] = 2
        if (options['Number of elements across'] < 2) :
            options['Number of elements across'] = 2
        if (options['Wall thickness left'] < 0.0) :
            options['Wall thickness left'] = 0.0
        elif (options['Wall thickness left'] > 0.5) :
            options['Wall thickness left'] = 0.5
        if (options['Wall thickness right'] < 0.0) :
            options['Wall thickness right'] = 0.0
        elif (options['Wall thickness right'] > 0.5) :
            options['Wall thickness right'] = 0.5
        if (options['Apex scale factor identifier offset'] < 0) :
            options['Apex scale factor identifier offset'] = 0

    @staticmethod
    def generateMesh(region, options):
        """
        :param region: Zinc region to define model in. Must be empty.
        :param options: Dict containing options. See getDefaultOptions().
        :return: None
        """
        elementsCountUp = options['Number of elements up']
        elementsCountAcross = options['Number of elements across']
        wallThickness = [ options['Wall thickness left'], options['Wall thickness right'] ]
        apexScaleFactorIdentifierOffset = 10000
        useCrossDerivatives = options['Use cross derivatives']

        fm = region.getFieldmodule()
        fm.beginChange()
        coordinates = fm.createFieldFiniteElement(3)
        coordinates.setName('coordinates')
        coordinates.setManaged(True)
        coordinates.setTypeCoordinate(True)
        coordinates.setCoordinateSystemType(Field.COORDINATE_SYSTEM_TYPE_RECTANGULAR_CARTESIAN)
        coordinates.setComponentName(1, 'x')
        coordinates.setComponentName(2, 'y')
        coordinates.setComponentName(3, 'z')

        nodes = fm.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        nodetemplateApex = nodes.createNodetemplate()
        nodetemplateApex.defineField(coordinates)
        nodetemplateApex.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_VALUE, 1)
        nodetemplateApex.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS1, 1)
        nodetemplateApex.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS2, 1)
        nodetemplateApex.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS3, 1)
        if useCrossDerivatives:
            nodetemplate = nodes.createNodetemplate()
            nodetemplate.defineField(coordinates)
            nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_VALUE, 1)
            nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS1, 1)
            nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS2, 1)
            nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D2_DS1DS2, 1)
            nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D_DS3, 1)
            nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D2_DS1DS3, 1)
            nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D2_DS2DS3, 1)
            nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_D3_DS1DS2DS3, 1)
        else:
            nodetemplate = nodetemplateApex

        mesh = fm.findMeshByDimension(3)
        tricubicHermiteBasis = fm.createElementbasis(3, Elementbasis.FUNCTION_TYPE_CUBIC_HERMITE)

        eft = mesh.createElementfieldtemplate(tricubicHermiteBasis)
        if not useCrossDerivatives:
            for n in range(8):
                eft.setFunctionNumberOfTerms(n*8 + 4, 0)
                eft.setFunctionNumberOfTerms(n*8 + 6, 0)
                eft.setFunctionNumberOfTerms(n*8 + 7, 0)
                eft.setFunctionNumberOfTerms(n*8 + 8, 0)

        eftOuter = mesh.createElementfieldtemplate(tricubicHermiteBasis)
        # general linear map at 4 nodes for one derivative
        eftOuter.setNumberOfLocalScaleFactors(8)
        for s in range(8):
            eftOuter.setScaleFactorType(s + 1, Elementfieldtemplate.SCALE_FACTOR_TYPE_NODE_GENERAL)
            eftOuter.setScaleFactorIdentifier(s + 1, (s % 2) + 1)
        if useCrossDerivatives:
            noCrossRange = range(4)
        else:
            noCrossRange = range(8)
        for n in noCrossRange:
            eftOuter.setFunctionNumberOfTerms(n*8 + 4, 0)
            eftOuter.setFunctionNumberOfTerms(n*8 + 6, 0)
            eftOuter.setFunctionNumberOfTerms(n*8 + 7, 0)
            eftOuter.setFunctionNumberOfTerms(n*8 + 8, 0)
        # general linear map dxi1 from ds1 + ds3 for first 4 nodes
        for n in range(4):
            ln = n + 1
            eftOuter.setFunctionNumberOfTerms(n*8 + 2, 2)
            eftOuter.setTermNodeParameter(n*8 + 2, 1, ln, Node.VALUE_LABEL_D_DS1, 1)
            eftOuter.setTermScaling(n*8 + 2, 1, [n*2 + 1])
            eftOuter.setTermNodeParameter(n*8 + 2, 2, ln, Node.VALUE_LABEL_D_DS3, 1)
            eftOuter.setTermScaling(n*8 + 2, 2, [n*2 + 2])

        eftOuterApex0 = mesh.createElementfieldtemplate(tricubicHermiteBasis)
        # general linear map at 4 nodes for one derivative
        eftOuterApex0.setNumberOfLocalScaleFactors(8)
        for s in range(8):
            eftOuterApex0.setScaleFactorType(s + 1, Elementfieldtemplate.SCALE_FACTOR_TYPE_NODE_GENERAL)
            scaleFactorId = (s % 2) + 1
            if s < 4:
                scaleFactorId += apexScaleFactorIdentifierOffset
            eftOuterApex0.setScaleFactorIdentifier(s + 1, scaleFactorId)
        if useCrossDerivatives:
            noCrossRange = range(4)
        else:
            noCrossRange = range(8)
        for n in noCrossRange:
            eftOuterApex0.setFunctionNumberOfTerms(n*8 + 4, 0)
            eftOuterApex0.setFunctionNumberOfTerms(n*8 + 6, 0)
            eftOuterApex0.setFunctionNumberOfTerms(n*8 + 7, 0)
            eftOuterApex0.setFunctionNumberOfTerms(n*8 + 8, 0)
        # general linear map dxi1 from ds1 + ds3 for first 4 nodes
        for n in range(4):
            ln = n + 1
            eftOuterApex0.setFunctionNumberOfTerms(n*8 + 2, 2)
            eftOuterApex0.setTermNodeParameter(n*8 + 2, 1, ln, Node.VALUE_LABEL_D_DS1, 1)
            eftOuterApex0.setTermScaling(n*8 + 2, 1, [n*2 + 1])
            eftOuterApex0.setTermNodeParameter(n*8 + 2, 2, ln, Node.VALUE_LABEL_D_DS3, 1)
            eftOuterApex0.setTermScaling(n*8 + 2, 2, [n*2 + 2])
        #print('eftOuterApex0', eftOuterApex0.validate())

        eftOuterApex1 = mesh.createElementfieldtemplate(tricubicHermiteBasis)
        eftOuterApex2 = mesh.createElementfieldtemplate(tricubicHermiteBasis)
        i = 0
        for eftOuterApex in [ eftOuterApex1, eftOuterApex2 ]:
            i += 1
            # general linear map at 4 nodes for one derivative
            eftOuterApex.setNumberOfLocalScaleFactors(9)
            # GRC: allow scale factor identifier for global -1.0 to be prescribed
            eftOuterApex.setScaleFactorType(1, Elementfieldtemplate.SCALE_FACTOR_TYPE_GLOBAL_GENERAL)
            eftOuterApex.setScaleFactorIdentifier(1, 1)
            for s in range(8):
                eftOuterApex.setScaleFactorType(s + 2, Elementfieldtemplate.SCALE_FACTOR_TYPE_NODE_GENERAL)
                scaleFactorId = (s % 2) + 1
                if ((i == 1) and (s < 4)) or ((i == 2) and (s >= 4)):
                    scaleFactorId += apexScaleFactorIdentifierOffset
                result = eftOuterApex.setScaleFactorIdentifier(s + 2, scaleFactorId)
            if useCrossDerivatives:
                noCrossRange = range(4)
            else:
                noCrossRange = range(8)
            for n in noCrossRange:
                eftOuterApex.setFunctionNumberOfTerms(n*8 + 4, 0)
                eftOuterApex.setFunctionNumberOfTerms(n*8 + 6, 0)
                eftOuterApex.setFunctionNumberOfTerms(n*8 + 7, 0)
                eftOuterApex.setFunctionNumberOfTerms(n*8 + 8, 0)
            # general linear map dxi1 from ds1 + ds3 for first 4 nodes
            for n in range(4):
                ln = n + 1
                eftOuterApex.setFunctionNumberOfTerms(n*8 + 2, 2)
                eftOuterApex.setTermNodeParameter(n*8 + 2, 1, ln, Node.VALUE_LABEL_D_DS1, 1)
                negate = (i == 1) and (n < 2)  # False  # ((i == 1) and (n < 2)) or ((i == 2) and (n >= 2))
                eftOuterApex.setTermScaling(n*8 + 2, 1, [1, n*2 + 2] if negate else [n*2 + 2])
                eftOuterApex.setTermNodeParameter(n*8 + 2, 2, ln, Node.VALUE_LABEL_D_DS3, 1)
                eftOuterApex.setTermScaling(n*8 + 2, 2, [1, n*2 + 3] if negate else [n*2 + 3])
            if i == 1:
                negateNodes1 = [ 4, 5 ]
                negateNodes2 = [ 0, 1, 4, 5 ]
            else:
                negateNodes1 = [ 6, 7 ]
                negateNodes2 = [ 2, 3, 6, 7]
            for n in negateNodes1:
                eftOuterApex.setTermScaling(n*8 + 2, 1, [1])
            for n in negateNodes2:
                eftOuterApex.setTermScaling(n*8 + 3, 1, [1])
        #print('eftOuterApex1', eftOuterApex1.validate())
        #print('eftOuterApex2', eftOuterApex2.validate())

        eftInner1 = mesh.createElementfieldtemplate(tricubicHermiteBasis)
        # negate dxi1 plus general linear map at 4 nodes for one derivative
        eftInner1.setNumberOfLocalScaleFactors(9)
        # GRC: allow scale factor identifier for global -1.0 to be prescribed
        eftInner1.setScaleFactorType(1, Elementfieldtemplate.SCALE_FACTOR_TYPE_GLOBAL_GENERAL)
        eftInner1.setScaleFactorIdentifier(1, 1)
        for s in range(8):
            eftInner1.setScaleFactorType(s + 2, Elementfieldtemplate.SCALE_FACTOR_TYPE_NODE_GENERAL)
            eftInner1.setScaleFactorIdentifier(s + 2, (s % 2) + 1)
        if useCrossDerivatives:
            noCrossRange = [ 0, 2, 4, 6 ]
        else:
            noCrossRange = range(8)
        for n in noCrossRange:
            eftInner1.setFunctionNumberOfTerms(n*8 + 4, 0)
            eftInner1.setFunctionNumberOfTerms(n*8 + 6, 0)
            eftInner1.setFunctionNumberOfTerms(n*8 + 7, 0)
            eftInner1.setFunctionNumberOfTerms(n*8 + 8, 0)
        # general linear map dxi3 from ds1 + ds3 for 4 odd nodes
        s = 0
        for n in [ 0, 2, 4, 6 ]:
            ln = n + 1
            eftInner1.setFunctionNumberOfTerms(n*8 + 5, 2)
            eftInner1.setTermNodeParameter(n*8 + 5, 1, ln, Node.VALUE_LABEL_D_DS1, 1)
            eftInner1.setTermScaling(n*8 + 5, 1, [s*2 + 2])
            eftInner1.setTermNodeParameter(n*8 + 5, 2, ln, Node.VALUE_LABEL_D_DS3, 1)
            eftInner1.setTermScaling(n*8 + 5, 2, [s*2 + 3])
            s += 1
        # negate d/dxi1 at 2 nodes
        for n in [4, 6]:
            result = eftInner1.setTermScaling(n*8 + 2, 1, [1])

        eftInner2 = mesh.createElementfieldtemplate(tricubicHermiteBasis)
        # negate dxi1 plus general linear map at 4 nodes for one derivative
        eftInner2.setNumberOfLocalScaleFactors(9)
        # GRC: allow scale factor identifier for global -1.0 to be prescribed
        eftInner2.setScaleFactorType(1, Elementfieldtemplate.SCALE_FACTOR_TYPE_GLOBAL_GENERAL)
        eftInner2.setScaleFactorIdentifier(1, 1)
        for s in range(8):
            eftInner2.setScaleFactorType(s + 2, Elementfieldtemplate.SCALE_FACTOR_TYPE_NODE_GENERAL)
            eftInner2.setScaleFactorIdentifier(s + 2, (s % 2) + 1)
        if useCrossDerivatives:
            noCrossRange = [ 1, 3, 5, 7 ]
        else:
            noCrossRange = range(8)
        for n in noCrossRange:
            eftInner2.setFunctionNumberOfTerms(n*8 + 4, 0)
            eftInner2.setFunctionNumberOfTerms(n*8 + 6, 0)
            eftInner2.setFunctionNumberOfTerms(n*8 + 7, 0)
            eftInner2.setFunctionNumberOfTerms(n*8 + 8, 0)
        # general linear map dxi3 from ds1 + ds3 for 4 even nodes
        s = 0
        for n in [ 1, 3, 5, 7 ]:
            ln = n + 1
            eftInner2.setFunctionNumberOfTerms(n*8 + 5, 2)
            eftInner2.setTermNodeParameter(n*8 + 5, 1, ln, Node.VALUE_LABEL_D_DS1, 1)
            eftInner2.setTermScaling(n*8 + 5, 1, [1, s*2 + 2])
            eftInner2.setTermNodeParameter(n*8 + 5, 2, ln, Node.VALUE_LABEL_D_DS3, 1)
            eftInner2.setTermScaling(n*8 + 5, 2, [1, s*2 + 3])
            s += 1
        # negate d/dxi1 at 2 nodes
        for n in [5, 7]:
            eftInner2.setTermScaling(n*8 + 2, 1, [1])

        elementtemplate = mesh.createElementtemplate()
        elementtemplate.setElementShapeType(Element.SHAPE_TYPE_CUBE)
        result = elementtemplate.defineField(coordinates, -1, eft)

        elementtemplateOuter = mesh.createElementtemplate()
        elementtemplateOuter.setElementShapeType(Element.SHAPE_TYPE_CUBE)
        result = elementtemplateOuter.defineField(coordinates, -1, eftOuter)

        elementtemplateOuterApex0 = mesh.createElementtemplate()
        elementtemplateOuterApex0.setElementShapeType(Element.SHAPE_TYPE_CUBE)
        result = elementtemplateOuterApex0.defineField(coordinates, -1, eftOuterApex0)
        elementtemplateOuterApex1 = mesh.createElementtemplate()
        elementtemplateOuterApex1.setElementShapeType(Element.SHAPE_TYPE_CUBE)
        result = elementtemplateOuterApex1.defineField(coordinates, -1, eftOuterApex1)
        elementtemplateOuterApex2 = mesh.createElementtemplate()
        elementtemplateOuterApex2.setElementShapeType(Element.SHAPE_TYPE_CUBE)
        result = elementtemplateOuterApex2.defineField(coordinates, -1, eftOuterApex2)
        #print(result, 'elementtemplateOuterApex2.defineField')

        elementtemplateInner1 = mesh.createElementtemplate()
        elementtemplateInner1.setElementShapeType(Element.SHAPE_TYPE_CUBE)
        result = elementtemplateInner1.defineField(coordinates, -1, eftInner1)
        elementtemplateInner2 = mesh.createElementtemplate()
        elementtemplateInner2.setElementShapeType(Element.SHAPE_TYPE_CUBE)
        result = elementtemplateInner2.defineField(coordinates, -1, eftInner2)

        cache = fm.createFieldcache()

        # create nodes
        nodeIdentifier = 1
        radiansPerElementUp = math.pi/elementsCountUp
        #radiansPerElementAcross = math.pi/elementsCountAcross
        angle_radians = math.pi/4
        sin_angle_radians = math.sin(angle_radians)
        cos_angle_radians = math.cos(angle_radians)
        x = [ 0.0, 0.0, 0.0 ]
        dx_ds1 = [ 0.0, 0.0, 0.0 ]
        dx_ds2 = [ 0.0, 0.0, 0.0 ]
        dx_ds3 = [ 0.0, 0.0, 0.0 ]
        zero = [ 0.0, 0.0, 0.0 ]
        wallThicknessSeptum = wallThickness[0]
        #wallThicknessMin = min(wallThickness)
        wallThicknessMax = max(wallThickness)
        for n3 in range(2):
            sign = -1.0 if (n3 == 0) else 1.0
            radiusY = 0.5*wallThicknessSeptum
            radiusX = 0.5 - wallThicknessMax
            sideBulge = 8.0*radiusY*radiusX/elementsCountAcross

            # create two bottom apex nodes
            radius = radiusX + wallThickness[n3]
            x[0] = 0.0
            x[1] = -sign*radiusY
            if wallThickness[0] > wallThickness[1]:
                x[1] -= sideBulge
            elif wallThickness[0] < wallThickness[1]:
                x[1] += sideBulge
            x[2] = -radius
            node = nodes.createNode(nodeIdentifier, nodetemplateApex)
            cache.setNode(node)
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, x)
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS1, 1, [ 0.0, wallThicknessSeptum, 0.0 ])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS2, 1, [ radius*radiansPerElementUp, 0.0, 0.0 ])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS3, 1, [ 0.0, 0.0, -wallThickness[n3] ])
            nodeIdentifier = nodeIdentifier + 1

            radius = radiusX
            x[0] = 0.0
            x[1] = -sign*(radiusY + sideBulge)
            x[2] = -radius
            dx_ds3[0] = 0.0
            if ((n3 == 1) and (wallThickness[0] > wallThickness[1])) or \
                ((n3 == 0) and (wallThickness[0] < wallThickness[1])):
                dx_ds3[1] = 0.0
                dx_ds3[2] = -wallThickness[n3]
            else:
                dx_ds3[1] = sign*wallThickness[n3]*cos_angle_radians
                dx_ds3[2] = -wallThickness[n3]*sin_angle_radians
            node = nodes.createNode(nodeIdentifier, nodetemplateApex)
            cache.setNode(node)
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, x)
            mag1 = 2.0*radius/elementsCountAcross
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS1, 1, [ 0.0, mag1*sin_angle_radians, sign*mag1*cos_angle_radians ])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS2, 1, [ radius*radiansPerElementUp, 0.0, 0.0 ])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS3, 1, dx_ds3)
            nodeIdentifier = nodeIdentifier + 1

            # create regular rows between apexes
            for n2 in range(1, elementsCountUp):
                xi2 = n2/elementsCountUp
                radiansUp = n2*radiansPerElementUp
                cosRadiansUp = math.cos(radiansUp)
                sinRadiansUp = math.sin(radiansUp)
                x[2] = 0.0  # GRC: must set
                for n1 in range(elementsCountAcross + 3):
                    if (n1 == 0) or (n1 == (elementsCountAcross + 2)):
                        flip = -1.0 if (n1 == 0) else 1.0
                        radius = radiusX + wallThickness[n3]
                        x = [ radius*sinRadiansUp, -sign*radiusY, -radius*cosRadiansUp ]
                        if n1 == 0:
                            x[0] = -x[0]
                        if wallThickness[0] > wallThickness[1]:
                            x[1] -= sideBulge
                        elif wallThickness[0] < wallThickness[1]:
                            x[1] += sideBulge
                        dx_ds1 = [ 0.0, flip*wallThicknessSeptum, 0.0 ]
                        mag2 = radius*radiansPerElementUp
                        dx_ds2 = [ mag2*cosRadiansUp*flip, 0.0, mag2*sinRadiansUp ]
                        mag3 = wallThickness[n3]*flip
                        dx_ds3 = [ mag3*sinRadiansUp, 0.0, -mag3*cosRadiansUp*flip ]
                    elif (n1 == 1) or (n1 == (elementsCountAcross + 1)):
                        flip = -1.0 if (n1 == 1) else 1.0
                        radius = radiusX
                        x[0] = flip*sinRadiansUp*radius
                        x[1] = sign*(-radiusY - sideBulge)
                        x[2] = -cosRadiansUp*radius
                        mag1 = 2.0*radius/elementsCountAcross
                        dx_ds1 = [ -sign*sinRadiansUp*mag1*cos_angle_radians, flip*mag1*sin_angle_radians, flip*sign*cosRadiansUp*mag1*cos_angle_radians ]
                        mag2 = radius*radiansPerElementUp
                        dx_ds2 = [ mag2*cosRadiansUp*flip, 0.0, mag2*sinRadiansUp ]
                        mag3 = wallThickness[n3]
                        if ((n3 == 1) and (wallThickness[0] > wallThickness[1])) or \
                            ((n3 == 0) and (wallThickness[0] < wallThickness[1])):
                            dx_ds3 = [ flip*sinRadiansUp*mag3, 0.0, -cosRadiansUp*mag3 ]
                        else:
                            dx_ds3 = [ flip*sinRadiansUp*mag3*sin_angle_radians, sign*mag3*cos_angle_radians, -cosRadiansUp*mag3*sin_angle_radians ]
                        if n1 == 1:
                            # Prepare for interpolating interior points
                            v1 = ( -sinRadiansUp*radius, -sign*radiusY, -cosRadiansUp*radius )
                            mag = math.sqrt(dx_ds1[0]*dx_ds1[0] + dx_ds1[2]*dx_ds1[2])
                            scale1 = -sign/mag*radius*sinRadiansUp
                            d1 = ( scale1*dx_ds1[0], 0.0, scale1*dx_ds1[2] )
                            v2 = ( 0.0, -sign*radiusY, 2.0*(xi2 - 0.5)*radius )
                            d2 = ( radius*sinRadiansUp, 0.0, 0.0 )
                            v1x = ( mag2*cosRadiansUp*flip, 0.0, mag2*sinRadiansUp )
                            d1x = ( 0.0, 0.0, 0.0 )
                            v2x = ( 0.0, 0.0, 2.0*radiusX/elementsCountUp )
                            d2x = ( 0.0, 0.0, 0.0 )
                    else:
                        xi = (n1 - 1)/elementsCountAcross
                        cxi = xi*2.0
                        flipHalf = (n1 - 1)*2 > elementsCountAcross
                        if flipHalf:
                            cxi = 2.0 - cxi
                        v = interpolateCubicHermite(v1, d1, v2, d2, cxi)
                        d = interpolateCubicHermiteDerivative(v1, d1, v2, d2, cxi)
                        if flipHalf:
                            x = [ -v[0], v[1], v[2] ]
                            dx_ds1 = [ 2.0*d[0]/elementsCountAcross, 0.0, -2.0*d[2]/elementsCountAcross ]
                        else:
                            x = [ v[0], v[1], v[2] ]
                            dx_ds1 = [ 2.0*d[0]/elementsCountAcross, 0.0, 2.0*d[2]/elementsCountAcross ]
                        dx = interpolateCubicHermite(v1x, d1x, v2x, d2x, cxi)
                        if flipHalf:
                            dx_ds2 = [ -dx[0], 0.0, dx[2] ]
                        else:
                            dx_ds2 = [ dx[0], 0.0, dx[2] ]
                        dx_ds3 = [ 0.0, -wallThicknessSeptum, 0.0 ]
                    node = nodes.createNode(nodeIdentifier, nodetemplate)
                    cache.setNode(node)
                    coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, x)
                    coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS1, 1, dx_ds1)
                    coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS2, 1, dx_ds2)
                    coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS3, 1, dx_ds3)
                    if useCrossDerivatives:
                        coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D2_DS1DS2, 1, zero)
                        coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D2_DS1DS3, 1, zero)
                        coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D2_DS2DS3, 1, zero)
                        coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D3_DS1DS2DS3, 1, zero)
                    nodeIdentifier = nodeIdentifier + 1

            # create two top apex nodes

            radius = radiusX
            x[0] = 0.0
            x[1] = -sign*(radiusY + sideBulge)
            x[2] = radius
            dx_ds3[0] = 0.0
            if ((n3 == 1) and (wallThickness[0] > wallThickness[1])) or \
                ((n3 == 0) and (wallThickness[0] < wallThickness[1])):
                dx_ds3[1] = 0.0
                dx_ds3[2] = wallThickness[n3]
            else:
                dx_ds3[1] = sign*wallThickness[n3]*cos_angle_radians
                dx_ds3[2] = wallThickness[n3]*sin_angle_radians
            node = nodes.createNode(nodeIdentifier, nodetemplateApex)
            cache.setNode(node)
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, x)
            mag1 = 2.0*radius/elementsCountAcross
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS1, 1, [ 0.0, -mag1*sin_angle_radians, sign*mag1*cos_angle_radians ])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS2, 1, [ radius*radiansPerElementUp, 0.0, 0.0 ])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS3, 1, dx_ds3)
            nodeIdentifier = nodeIdentifier + 1

            radius = radiusX + wallThickness[n3]
            x[0] = 0.0
            x[1] = -sign*radiusY
            if wallThickness[0] > wallThickness[1]:
                x[1] -= sideBulge
            elif wallThickness[0] < wallThickness[1]:
                x[1] += sideBulge
            x[2] = radius
            node = nodes.createNode(nodeIdentifier, nodetemplateApex)
            cache.setNode(node)
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_VALUE, 1, x)
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS1, 1, [ 0.0, -wallThicknessSeptum, 0.0 ])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS2, 1, [ radius*radiansPerElementUp, 0.0, 0.0 ])
            coordinates.setNodeParameters(cache, -1, Node.VALUE_LABEL_D_DS3, 1, [ 0.0, 0.0, wallThickness[n3] ])
            nodeIdentifier = nodeIdentifier + 1

        scaleFactorsOuter = [
            math.cos(0.25*math.pi), math.cos(0.25*math.pi), math.cos(0.25*math.pi), -math.cos(0.25*math.pi),
            math.cos(0.25*math.pi), math.cos(0.25*math.pi), math.cos(0.25*math.pi), -math.cos(0.25*math.pi)
        ]
        scaleFactorsOuterApex1 = [ -1.0,
            -math.cos(0.25*math.pi), math.cos(0.25*math.pi), -math.cos(0.25*math.pi), -math.cos(0.25*math.pi),
            math.cos(0.25*math.pi), math.cos(0.25*math.pi), math.cos(0.25*math.pi), -math.cos(0.25*math.pi)
        ]
        scaleFactorsOuterApex2 = [ -1.0,
            math.cos(0.25*math.pi), math.cos(0.25*math.pi), math.cos(0.25*math.pi), -math.cos(0.25*math.pi),
            -math.cos(0.25*math.pi), math.cos(0.25*math.pi), -math.cos(0.25*math.pi), -math.cos(0.25*math.pi)
        ]
        scaleFactorsInner1 = [ -1.0,
            math.cos(0.25*math.pi), math.cos(0.25*math.pi), math.cos(0.25*math.pi), math.cos(0.25*math.pi),
            math.cos(0.25*math.pi), -math.cos(0.25*math.pi), math.cos(0.25*math.pi), -math.cos(0.25*math.pi)
        ]

        # create elements
        elementIdentifier = 1
        rno = elementsCountAcross + 3
        wno = (elementsCountUp - 1)*rno + 4

        # bottom apex row
        element = mesh.createElement(elementIdentifier, elementtemplateOuterApex1)
        bni11 = 2
        bni12 = 2 + wno
        bni21 = 4
        bni22 = 4 + wno
        nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 - 1, bni12 - 1, bni21 - 1, bni22 - 1 ]
        result = element.setNodesByIdentifier(eftOuterApex1, nodeIdentifiers)
        #print(result, 'bottom outer apex element 1', elementIdentifier, nodeIdentifiers)
        element.setScaleFactors(eftOuterApex1, scaleFactorsOuterApex1)
        elementIdentifier = elementIdentifier + 1

        element = mesh.createElement(elementIdentifier, elementtemplateOuterApex0)
        bni11 = wno + 2
        bni12 = 2
        bni21 = wno + rno + 1
        bni22 = rno + 1
        nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 - 1, bni12 - 1, bni21 + 1, bni22 + 1 ]
        result = element.setNodesByIdentifier(eftOuterApex0, nodeIdentifiers)
        #print(result, 'bottom outer apex element 2', elementIdentifier, nodeIdentifiers)
        element.setScaleFactors(eftOuterApex0, scaleFactorsOuter)
        elementIdentifier = elementIdentifier + 1

        for e2 in range(0, elementsCountUp - 2):
            bn = e2*rno + 2
            element = mesh.createElement(elementIdentifier, elementtemplateOuter)
            bni11 = bn + 2
            bni12 = bn + wno + 2
            bni21 = bn + rno + 2
            bni22 = bn + wno + rno + 2
            nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 - 1, bni12 - 1, bni21 - 1, bni22 - 1 ]
            result = element.setNodesByIdentifier(eftOuter, nodeIdentifiers)
            #print(result, 'outer1 element', elementIdentifier, nodeIdentifiers)
            element.setScaleFactors(eftOuter, scaleFactorsOuter)
            elementIdentifier = elementIdentifier + 1

            element = mesh.createElement(elementIdentifier, elementtemplateInner1)
            bni11 = bn + 2
            bni12 = bn + 3
            bni21 = bn + rno + 2
            bni22 = bn + rno + 3
            nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 + wno, bni12 + wno, bni21 + wno, bni22 + wno ]
            result = element.setNodesByIdentifier(eftInner1, nodeIdentifiers)
            #print(result, 'inner1 element', elementIdentifier, 'nodes', nodeIdentifiers)
            result = element.setScaleFactor(eftInner1, 1, -1.0)
            #print(result, 'element', elementIdentifier, 'scale factors', scaleFactorsInner1)
            elementIdentifier = elementIdentifier + 1

            for e1 in range(elementsCountAcross - 2):
                element = mesh.createElement(elementIdentifier, elementtemplate)
                bni11 = bn + e1 + 3
                bni12 = bn + e1 + 4
                bni21 = bn + rno + e1 + 3
                bni22 = bn + rno + e1 + 4
                nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 + wno, bni12 + wno, bni21 + wno, bni22 + wno ]
                result = element.setNodesByIdentifier(eft, nodeIdentifiers)
                #print(result, 'element', elementIdentifier, 'nodes', nodeIdentifiers)
                elementIdentifier = elementIdentifier + 1

            element = mesh.createElement(elementIdentifier, elementtemplateInner2)
            bni11 = bn + rno - 2
            bni12 = bn + rno - 1
            bni21 = bn + 2*rno -2
            bni22 = bn + 2*rno - 1
            nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 + wno, bni12 + wno, bni21 + wno, bni22 + wno ]
            result = element.setNodesByIdentifier(eftInner2, nodeIdentifiers)
            #print(result, 'element', elementIdentifier, 'nodes', nodeIdentifiers)
            result = element.setScaleFactor(eftInner2, 1, -1.0)
            #print(result, 'element', elementIdentifier, 'scale factors', scaleFactorsInner1)
            elementIdentifier = elementIdentifier + 1

            element = mesh.createElement(elementIdentifier, elementtemplateOuter)
            bni11 = bn + wno + rno - 1
            bni12 = bn + rno - 1
            bni21 = bn + wno + 2*rno - 1
            bni22 = bn + 2*rno - 1
            nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 + 1, bni12 + 1, bni21 + 1, bni22 + 1 ]
            result = element.setNodesByIdentifier(eftOuter, nodeIdentifiers)
            #print(result, 'element', elementIdentifier, nodeIdentifiers)
            element.setScaleFactors(eftOuter, scaleFactorsOuter)
            elementIdentifier = elementIdentifier + 1

        # top apex row
        element = mesh.createElement(elementIdentifier, elementtemplateOuterApex0)
        bni11 = wno - rno
        bni12 = 2*wno - rno
        bni21 = wno - 1
        bni22 = 2*wno - 1
        nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 - 1, bni12 - 1, bni21 + 1, bni22 + 1 ]
        result = element.setNodesByIdentifier(eftOuterApex0, nodeIdentifiers)
        #print(result, 'top outer apex element 1', elementIdentifier, nodeIdentifiers)
        element.setScaleFactors(eftOuterApex0, scaleFactorsOuter)
        elementIdentifier = elementIdentifier + 1

        element = mesh.createElement(elementIdentifier, elementtemplateOuterApex2)
        bni11 = 2*wno - 3
        bni12 = wno - 3
        bni21 = 2*wno - 1
        bni22 = wno - 1
        nodeIdentifiers = [ bni11, bni12, bni21, bni22, bni11 + 1, bni12 + 1, bni21 + 1, bni22 + 1 ]
        result = element.setNodesByIdentifier(eftOuterApex2, nodeIdentifiers)
        #print(result, 'top outer apex element 2', elementIdentifier, nodeIdentifiers)
        result = element.setScaleFactors(eftOuterApex2, scaleFactorsOuterApex2)
        #print(result, 'top outer apex element 2 scale', elementIdentifier, scaleFactorsOuterApex2)

        elementIdentifier = elementIdentifier + 1

        fm.endChange()
